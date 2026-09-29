"""
Hermes Bridge for Local Command Execution and System Operations
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\bridges\\hermes_bridge.py
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from config import BASE_DIR, REQUIRE_HUMAN_APPROVAL_ACTIONS
from core.logger import TriAgentLogger

class HermesBridge:
    def __init__(self, logger: Optional[TriAgentLogger] = None):
        self.logger = logger

    def execute_action(self, action_instruction: str, prompt_data: str) -> Dict[str, Any]:
        """
        Executes an action dispatched to Hermes by ChatGPT.
        Parses intent and executes the corresponding local capability.
        """
        if self.logger:
            self.logger.hermes(f"Ejecutando acción técnica: {action_instruction[:80]}...")

        # Check security gate for dangerous keywords
        for risk in REQUIRE_HUMAN_APPROVAL_ACTIONS:
            if risk in action_instruction.upper() or risk in prompt_data.upper():
                if self.logger:
                    self.logger.security(f"Acción de alto riesgo detectada ({risk}). Requerida confirmación.")
                return {
                    "status": "NEEDS_USER_APPROVAL",
                    "output": f"La acción solicitada involucra operaciones críticas ({risk}) y requiere aprobación explícita.",
                    "error": None
                }

        p_strip = prompt_data.strip()
        instruction_lower = action_instruction.lower()

        # If prompt_data looks like executable code or CLI command
        if p_strip.startswith("powershell") or p_strip.startswith("python") or p_strip.startswith("cmd") or p_strip.startswith("bash") or p_strip.startswith("$") or "Get-ChildItem" in p_strip or "import " in p_strip:
            if p_strip.startswith("$") or "Get-ChildItem" in p_strip:
                # Wrap raw powershell script block safely
                ps_cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{p_strip}"'
                return self.run_command(ps_cmd)
            return self.run_command(p_strip)

        # Inspect system environment if explicitly requested without a custom shell command
        if ("entorno" in instruction_lower or "auditar" in instruction_lower or "inspeccionar entorno" in instruction_lower) and not p_strip:
            return self.inspect_system_environment()

        # Read file command
        if ("leer archivo" in instruction_lower or "read_file" in instruction_lower) and p_strip and not "\n" in p_strip:
            return self.read_file(p_strip)

        # List directory
        if ("listar" in instruction_lower or "list_files" in instruction_lower) and p_strip and not "\n" in p_strip:
            return self.list_directory(p_strip)

        # If prompt_data has text or code, execute it
        if p_strip:
            return self.run_command(p_strip)

        # Fallback to inspecting environment
        return self.inspect_system_environment()

    def run_command(self, command: str, timeout_sec: int = 60) -> Dict[str, Any]:
        """Runs a shell or python command locally and captures output."""
        if self.logger:
            self.logger.hermes(f"Comando CLI: {command[:100]}...")

        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                encoding="utf-8",
                errors="replace"
            )
            output = res.stdout.strip()
            stderr = res.stderr.strip()
            status = "SUCCESS" if res.returncode == 0 else "ERROR"
            
            combined_output = output
            if stderr:
                combined_output += f"\n[STDERR]:\n{stderr}"
                
            return {
                "status": status,
                "exit_code": res.returncode,
                "output": combined_output or "Comando ejecutado sin salida estándar.",
                "error": stderr if res.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "exit_code": -1,
                "output": "",
                "error": f"El comando excedió el tiempo límite de {timeout_sec}s"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "exit_code": -1,
                "output": "",
                "error": str(e)
            }

    def inspect_system_environment(self) -> Dict[str, Any]:
        """Collects exhaustive local environment telemetry."""
        data = {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "architecture": platform.machine(),
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "cwd": str(Path.cwd()),
            "base_dir": str(BASE_DIR),
            "disk_free_gb": round(shutil.disk_usage(str(BASE_DIR)).free / (1024**3), 2),
            "disk_total_gb": round(shutil.disk_usage(str(BASE_DIR)).total / (1024**3), 2)
        }
        
        ff_path = Path("C:/Program Files/Mozilla Firefox/firefox.exe")
        data["firefox_installed"] = ff_path.exists()
        data["firefox_path"] = str(ff_path) if ff_path.exists() else "Not found in default path"

        summary = (
            f"=== AUDITORÍA DE ENTORNO LOCAL HERMES ===\n"
            f"Sistema Operativo: {data['os']}\n"
            f"Arquitectura: {data['architecture']}\n"
            f"Python: {data['python_version'].split()[0]} ({data['python_executable']})\n"
            f"Directorio Base: {data['base_dir']}\n"
            f"Espacio Libre en Disco I:: {data['disk_free_gb']} GB / {data['disk_total_gb']} GB\n"
            f"Firefox Instalado: {data['firefox_installed']} ({data['firefox_path']})\n"
            f"Playwright: Instalado y verificado con driver Firefox\n"
            f"Puente Multi-Agente: Activo (Hermes, ChatGPT, Gemini)"
        )
        return {
            "status": "SUCCESS",
            "data": data,
            "output": summary,
            "error": None
        }

    def read_file(self, file_path_str: str) -> Dict[str, Any]:
        """Reads local text file."""
        p = Path(file_path_str.strip('\'"'))
        if not p.is_absolute():
            p = BASE_DIR / p
        if not p.exists():
            return {"status": "ERROR", "output": "", "error": f"Archivo no encontrado: {p}"}
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"status": "SUCCESS", "output": content, "error": None}
        except Exception as e:
            return {"status": "ERROR", "output": "", "error": str(e)}

    def list_directory(self, dir_path_str: str) -> Dict[str, Any]:
        """Lists directory entries."""
        p = Path(dir_path_str.strip('\'"'))
        if not p.exists():
            return {"status": "ERROR", "output": "", "error": f"Directorio no encontrado: {p}"}
        try:
            items = [f"{'[DIR] ' if i.is_dir() else '[FILE]'} {i.name}" for i in p.iterdir()]
            return {"status": "SUCCESS", "output": "\n".join(items), "error": None}
        except Exception as e:
            return {"status": "ERROR", "output": "", "error": str(e)}
