"""
Central Multi-Agent Orchestrator
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\orchestrator.py
"""
import time
from typing import Dict, Any, Optional
from pathlib import Path
from config import BASE_DIR, STATE_DIR, MAX_ITERATIONS
from core.protocol import parse_hf_response, format_action_envelope, format_gemini_result
from core.logger import TriAgentLogger
from core.state_manager import StateManager
from core.loop_controller import LoopController
from core.recovery_manager import RecoveryManager
from bridges.browser_controller import BrowserController
from bridges.chatgpt_bridge import ChatGPTBridge
from bridges.gemini_bridge import GeminiBridge
from bridges.hermes_bridge import HermesBridge

class TriAgentOrchestrator:
    def __init__(self, state_manager: StateManager, logger: Optional[TriAgentLogger] = None):
        self.state_mgr = state_manager
        self.logger = logger or TriAgentLogger(log_file=self.state_mgr.files["events"])
        self.logger.set_log_file(self.state_mgr.files["events"])
        
        # Subsystems
        self.loop_ctrl = LoopController()
        self.recovery_mgr = RecoveryManager(self.state_mgr, self.logger)
        self.browser_ctrl = BrowserController(logger=self.logger)
        
        # Bridges
        self.chatgpt = ChatGPTBridge(self.browser_ctrl, logger=self.logger)
        self.gemini = GeminiBridge(self.browser_ctrl, results_dir=self.state_mgr.results_dir, logger=self.logger)
        self.hermes = HermesBridge(logger=self.logger)
        
        self.is_running = False

    def run_mission(self, initial_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the main Tri-Agent Orchestration Loop until DONE or terminal state.
        """
        self.is_running = True
        mission_id = self.state_mgr.mission_id
        self.logger.banner(f"INICIANDO MISIÓN: {self.state_mgr.mission_data.get('title', mission_id)}")
        
        self.state_mgr.update_mission_status("RUNNING", current_agent="HERMES", target_agent="CHATGPT")
        
        instruction = initial_instruction or self.state_mgr.mission_data.get("description", "")
        if not instruction:
            err = "La misión no tiene instrucción inicial definida."
            self.logger.error(err)
            self.state_mgr.update_mission_status("ERROR")
            return {"status": "ERROR", "error": err}

        # Step 1: Initial dispatch from Hermes to ChatGPT
        current_message_to_chatgpt = (
            f"MISIÓN ASIGNADA:\n{instruction}\n\n"
            f"Por favor analiza los requerimientos, define el plan de acción inicial y emite la primera instrucción estructurada usando <HF_RESPONSE>."
        )
        
        iteration = self.state_mgr.mission_data.get("current_iteration", 0)
        is_first_turn = (iteration == 0)

        try:
            while self.is_running:
                iteration += 1
                self.state_mgr.update_mission_status("RUNNING", iteration=iteration)
                self.logger.info(f"--- ITERACIÓN MULTIAGENTE #{iteration} ---")

                # Check max iteration ceiling
                is_max, max_reason = self.loop_ctrl.check_iteration_limit(iteration)
                if is_max:
                    self.logger.warning(f"Límite de iteraciones alcanzado: {max_reason}")
                    self.state_mgr.update_mission_status("LOOP_DETECTED")
                    break

                # Check prompt loop
                is_loop_prompt, loop_p_reason = self.loop_ctrl.record_and_check_prompt(current_message_to_chatgpt)
                if is_loop_prompt:
                    self.logger.warning(f"Loop de prompts detectado: {loop_p_reason}")
                    self.state_mgr.update_mission_status("LOOP_DETECTED")
                    break

                # 1. SEND CONTEXT TO CHATGPT
                self.state_mgr.record_chatgpt_message(role="user", content=current_message_to_chatgpt)
                cg_response = self.chatgpt.send_prompt(current_message_to_chatgpt, is_first_turn=is_first_turn)
                is_first_turn = False

                if cg_response.get("status") == "ERROR":
                    self.logger.error(f"Fallo en ChatGPT Bridge: {cg_response.get('error')}")
                    exceeded, count = self.loop_ctrl.record_error("chatgpt_error")
                    if exceeded:
                        self.state_mgr.update_mission_status("ERROR")
                        break
                    time.sleep(3)
                    continue
                else:
                    self.loop_ctrl.reset_error("chatgpt_error")

                # Parse ChatGPT decision
                parsed = cg_response.get("parsed", {})
                raw_text = cg_response.get("raw_text", "")
                self.state_mgr.record_chatgpt_message(role="assistant", content=raw_text, parsed_protocol=parsed)

                status = parsed.get("status", "CONTINUE").upper()
                target_agent = parsed.get("target_agent", "HERMES").upper()
                task_summary = parsed.get("task_summary", "")
                next_action = parsed.get("next_action", "")
                prompt = parsed.get("prompt", "")

                self.logger.chatgpt(f"Decisión: STATUS={status} | TARGET={target_agent} | RESUMEN: {task_summary[:70]}")

                # Check if mission is complete
                if status == "DONE":
                    self.logger.banner("MISIÓN COMPLETADA CON ÉXITO")
                    self.logger.info(f"Resumen final de ChatGPT: {task_summary}")
                    self.state_mgr.update_mission_status("DONE", current_agent="CHATGPT", target_agent="NONE")
                    break

                if status in ["BLOCKED", "NEEDS_USER"]:
                    self.logger.warning(f"Misión requiere intervención de usuario: {task_summary}")
                    self.state_mgr.update_mission_status("NEEDS_USER")
                    break

                # 2. ROUTE TO TARGET AGENT
                if target_agent == "HERMES":
                    # Execute technical action locally
                    self.state_mgr.update_mission_status("RUNNING", current_agent="HERMES", target_agent="CHATGPT")
                    action_res = self.hermes.execute_action(action_instruction=next_action, prompt_data=prompt)
                    
                    action_id = self.state_mgr.record_action(
                        agent="HERMES",
                        input_data={"next_action": next_action, "prompt": prompt},
                        output_data=action_res.get("output"),
                        status=action_res.get("status", "SUCCESS"),
                        error=action_res.get("error")
                    )

                    # Build return feedback for ChatGPT
                    current_message_to_chatgpt = (
                        f"[HERMES_RESULT]\n"
                        f"ACTION_ID={action_id}\n"
                        f"STATUS={action_res.get('status')}\n"
                        f"OUTPUT:\n{action_res.get('output')}\n"
                        f"ERRORS={action_res.get('error') or 'NONE'}\n\n"
                        f"Evalúa este resultado y determina la siguiente acción."
                    )

                elif target_agent == "GEMINI":
                    # Delegate visual creation to Gemini
                    self.state_mgr.update_mission_status("RUNNING", current_agent="GEMINI", target_agent="CHATGPT")
                    gem_res = self.gemini.generate_visual(prompt=prompt, mission_id=mission_id)
                    
                    # Record artifact if image created
                    if gem_res.get("file_path"):
                        self.state_mgr.record_artifact(
                            filename=Path(gem_res["file_path"]).name,
                            file_path=gem_res["file_path"],
                            file_type=gem_res.get("file_type", "PNG"),
                            dimensions=gem_res.get("dimensions", "0x0"),
                            source_agent="GEMINI"
                        )

                    self.state_mgr.record_gemini_interaction(prompt=prompt, result=gem_res)
                    action_id = self.state_mgr.record_action(
                        agent="GEMINI",
                        input_data={"prompt": prompt},
                        output_data=gem_res.get("gemini_result_block"),
                        status=gem_res.get("status", "SUCCESS"),
                        error=gem_res.get("errors")
                    )

                    # Return formatted GEMINI_RESULT to ChatGPT
                    current_message_to_chatgpt = (
                        f"{gem_res.get('gemini_result_block')}\n\n"
                        f"GEMINI ha completado la generación visual requerida. "
                        f"Por favor revisa el resultado. Si cumple los objetivos de la misión, finaliza con STATUS=DONE. "
                        f"Si requiere ajustes de estilo o composición, solicita la siguiente versión con STATUS=CONTINUE."
                    )

                elif target_agent == "CHATGPT":
                    # ChatGPT requested internal continuation or clarification
                    current_message_to_chatgpt = (
                        f"Continuando con el plan. Siguiente paso: {next_action}\n"
                        f"Por favor procede con la siguiente instrucción usando <HF_RESPONSE>."
                    )

                # Small delay to keep UI smooth and prevent spamming
                time.sleep(2)

        except KeyboardInterrupt:
            self.recovery_mgr.handle_graceful_shutdown("Interrupción por teclado (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Error crítico en el orquestador: {e}")
            self.state_mgr.update_mission_status("ERROR")
        finally:
            self.browser_ctrl.close()
            self.state_mgr.save_all()

        return self.state_mgr.mission_data

    def stop(self):
        """Signals the orchestrator to halt."""
        self.is_running = False
        self.recovery_mgr.handle_graceful_shutdown("Detenido por el usuario")
