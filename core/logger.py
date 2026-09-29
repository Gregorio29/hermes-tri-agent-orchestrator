"""
Structured Logger for Hermes Tri-Agent Orchestrator
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\logger.py
"""
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# ANSI Color Codes for Windows / MSYS terminal
COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "DIM": "\033[2m",
    "CYAN": "\033[36m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "RED": "\033[31m",
    "WHITE": "\033[37m",
    "BG_BLUE": "\033[44m\033[37m",
    "BG_MAGENTA": "\033[45m\033[37m",
    "BG_GREEN": "\033[42m\033[30m",
    "BG_CYAN": "\033[46m\033[30m",
}

AGENT_BADGES = {
    "ORCHESTRATOR": f"{COLORS['BG_CYAN']} [ORCHESTRATOR] {COLORS['RESET']}",
    "HERMES": f"{COLORS['BG_BLUE']} [HERMES] {COLORS['RESET']}",
    "CHATGPT": f"{COLORS['BG_MAGENTA']} [CHATGPT] {COLORS['RESET']}",
    "GEMINI": f"{COLORS['BG_GREEN']} [GEMINI] {COLORS['RESET']}",
    "SECURITY": f"{COLORS['RED']}{COLORS['BOLD']} [SECURITY GATE] {COLORS['RESET']}",
    "STATE": f"{COLORS['YELLOW']} [STATE] {COLORS['RESET']}",
    "INFO": f"{COLORS['CYAN']} [INFO] {COLORS['RESET']}",
    "ERROR": f"{COLORS['RED']}{COLORS['BOLD']} [ERROR] {COLORS['RESET']}",
    "WARNING": f"{COLORS['YELLOW']}{COLORS['BOLD']} [WARNING] {COLORS['RESET']}",
}

class TriAgentLogger:
    def __init__(self, log_file: Optional[Path] = None, quiet: bool = False):
        self.log_file = Path(log_file) if log_file else None
        self.quiet = quiet
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def set_log_file(self, log_file: Path):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _format_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_to_file(self, raw_line: str):
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(raw_line + "\n")
            except Exception as e:
                print(f"[Logger Error] Could not write to {self.log_file}: {e}", file=sys.stderr)

    def log(self, agent: str, message: str, level: str = "INFO"):
        ts = self._format_time()
        badge = AGENT_BADGES.get(agent.upper(), f"[{agent.upper()}]")
        
        # Plain version for file log (strip ANSI colors)
        plain_agent = agent.upper()
        plain_line = f"[{ts}] [{plain_agent}] {message}"
        self._write_to_file(plain_line)
        
        if not self.quiet:
            print(f"{COLORS['DIM']}[{ts}]{COLORS['RESET']} {badge} {message}")

    def orchestrator(self, message: str):
        self.log("ORCHESTRATOR", message)

    def hermes(self, message: str):
        self.log("HERMES", message)

    def chatgpt(self, message: str):
        self.log("CHATGPT", message)

    def gemini(self, message: str):
        self.log("GEMINI", message)

    def security(self, message: str):
        self.log("SECURITY", message, level="WARNING")

    def state(self, message: str):
        self.log("STATE", message)

    def info(self, message: str):
        self.log("INFO", message)

    def warning(self, message: str):
        self.log("WARNING", message, level="WARNING")

    def error(self, message: str):
        self.log("ERROR", message, level="ERROR")

    def banner(self, title: str):
        border = "=" * 70
        ts = self._format_time()
        banner_str = f"\n{COLORS['CYAN']}{border}\n  {title.upper()} - {ts}\n{border}{COLORS['RESET']}\n"
        plain_str = f"\n{border}\n  {title.upper()} - {ts}\n{border}\n"
        self._write_to_file(plain_str)
        if not self.quiet:
            print(banner_str)

# Global default logger instance
default_logger = TriAgentLogger()
