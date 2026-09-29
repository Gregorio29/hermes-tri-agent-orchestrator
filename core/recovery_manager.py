"""
Recovery Manager and Checkpointing
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\recovery_manager.py
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from core.state_manager import StateManager
from core.logger import TriAgentLogger

class RecoveryManager:
    def __init__(self, state_manager: StateManager, logger: Optional[TriAgentLogger] = None):
        self.state_manager = state_manager
        self.logger = logger

    def diagnose_mission_health(self) -> Dict[str, Any]:
        """Inspects state files for consistency, interrupted actions, or anomalies."""
        data = self.state_manager.mission_data
        status = data.get("status", "UNKNOWN")
        actions = self.state_manager.actions
        
        last_action = actions[-1] if actions else None
        has_pending_action = False
        
        if last_action and last_action.get("status") in ["RUNNING", "PENDING"]:
            has_pending_action = True

        health_report = {
            "mission_id": self.state_manager.mission_id,
            "status": status,
            "total_actions": len(actions),
            "last_action_id": last_action.get("action_id") if last_action else None,
            "last_action_status": last_action.get("status") if last_action else None,
            "has_pending_action": has_pending_action,
            "can_resume": status in ["PAUSED", "BLOCKED", "ERROR", "INITIALIZED", "RUNNING"],
            "chatgpt_turns": len(self.state_manager.conversation_chatgpt),
            "gemini_turns": len(self.state_manager.conversation_gemini),
            "artifacts_count": len(self.state_manager.artifacts)
        }
        return health_report

    def prepare_resume(self) -> Dict[str, Any]:
        """Prepares state for resuming execution."""
        data = self.state_manager.mission_data
        actions = self.state_manager.actions
        
        # If last action was running/pending when terminated, mark it as recovered/retryable
        if actions and actions[-1].get("status") in ["RUNNING", "PENDING"]:
            actions[-1]["status"] = "INTERRUPTED"
            actions[-1]["error"] = "Proceso interrumpido antes de completar. Listo para reintento."
            
        self.state_manager.update_mission_status("RUNNING")
        if self.logger:
            self.logger.state(f"Misión {self.state_manager.mission_id} reanudada desde iteración {data.get('current_iteration', 0)}")
            
        return {
            "mission_id": self.state_manager.mission_id,
            "resumed_iteration": data.get("current_iteration", 0),
            "current_agent": data.get("current_agent", "HERMES"),
            "target_agent": data.get("next_target_agent", "CHATGPT")
        }

    def handle_graceful_shutdown(self, reason: str = "Interrupción de usuario"):
        """Saves current state cleanly on shutdown."""
        if self.logger:
            self.logger.warning(f"Deteniendo misión ordenadamente: {reason}")
        self.state_manager.update_mission_status("PAUSED")
        self.state_manager.save_all()
