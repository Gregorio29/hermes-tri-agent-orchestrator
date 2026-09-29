"""
Browser Controller for Persistent Firefox Automation
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\bridges\\browser_controller.py
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page
from config import (
    FIREFOX_PROFILE_DIR, FIREFOX_HEADLESS, VIEWPORT_WIDTH, 
    VIEWPORT_HEIGHT, USER_AGENT, CHATGPT_URL, GEMINI_URL, BROWSER_PAGE_TIMEOUT
)
from core.logger import TriAgentLogger

class BrowserController:
    def __init__(self, profile_dir: Optional[Path] = None, logger: Optional[TriAgentLogger] = None):
        self.profile_dir = Path(profile_dir) if profile_dir else FIREFOX_PROFILE_DIR
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self._is_headless = FIREFOX_HEADLESS

    def audit_environment(self) -> Dict[str, Any]:
        """Audits the environment for Firefox, profiles, Playwright, and Node."""
        report = {
            "firefox_installed": False,
            "firefox_paths": [],
            "firefox_profiles": [],
            "playwright_available": False,
            "playwright_firefox_driver": False,
            "node_available": False,
            "node_version": None,
            "dedicated_profile_path": str(self.profile_dir),
            "dedicated_profile_exists": self.profile_dir.exists()
        }
        
        # Check standard Firefox executable locations
        candidate_paths = [
            "C:/Program Files/Mozilla Firefox/firefox.exe",
            "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
            os.path.expandvars("%LOCALAPPDATA%/Mozilla Firefox/firefox.exe")
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                report["firefox_installed"] = True
                report["firefox_paths"].append(p)
                
        # Check Firefox profile dir in AppData
        ff_appdata = Path(os.path.expandvars("%APPDATA%/Mozilla/Firefox/Profiles"))
        if ff_appdata.exists():
            for prof in ff_appdata.iterdir():
                if prof.is_dir():
                    report["firefox_profiles"].append(prof.name)
                    
        # Check Node.js
        try:
            res = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                report["node_available"] = True
                report["node_version"] = res.stdout.strip()
        except Exception:
            pass
            
        # Check Playwright
        try:
            import playwright
            report["playwright_available"] = True
            with sync_playwright() as p:
                b = p.firefox.launch(headless=True)
                report["playwright_firefox_driver"] = True
                report["firefox_driver_version"] = b.version
                b.close()
        except Exception as e:
            report["playwright_error"] = str(e)
            
        return report

    def get_or_create_context(self, headless: Optional[bool] = None) -> BrowserContext:
        """Launches or reuses the persistent Firefox browser context."""
        if self.context is not None:
            return self.context

        if headless is not None:
            self._is_headless = headless

        if self.logger:
            mode_str = "Headless" if self._is_headless else "Visible (GUI)"
            self.logger.info(f"Iniciando Firefox ({mode_str}) con perfil persistente en {self.profile_dir}")

        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.firefox.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self._is_headless,
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            user_agent=USER_AGENT,
            accept_downloads=True
        )
        self.context.set_default_timeout(BROWSER_PAGE_TIMEOUT)
        return self.context

    def detect_sessions(self) -> Dict[str, Any]:
        """Detects current login and access status on ChatGPT and Gemini."""
        ctx = self.get_or_create_context(headless=True)
        session_info = {
            "chatgpt": {"accessible": False, "authenticated": False, "mode": "unknown"},
            "gemini": {"accessible": False, "authenticated": False, "mode": "unknown"}
        }
        
        # Check ChatGPT
        try:
            page_cg = ctx.new_page()
            page_cg.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            body_text = page_cg.inner_text("body")
            session_info["chatgpt"]["accessible"] = True
            # If Log In button is prominent or in header, it's guest mode; otherwise authenticated
            is_guest = "Log in" in body_text or "Sign up" in body_text
            session_info["chatgpt"]["authenticated"] = not is_guest
            session_info["chatgpt"]["mode"] = "authenticated" if not is_guest else "guest_ready"
            page_cg.close()
        except Exception as e:
            session_info["chatgpt"]["error"] = str(e)
            
        # Check Gemini
        try:
            page_gem = ctx.new_page()
            page_gem.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            body_text_gem = page_gem.inner_text("body")
            session_info["gemini"]["accessible"] = True
            is_guest_gem = "Sign in" in body_text_gem or "Inicia sesión" in body_text_gem
            session_info["gemini"]["authenticated"] = not is_guest_gem
            session_info["gemini"]["mode"] = "authenticated" if not is_guest_gem else "guest_ready"
            page_gem.close()
        except Exception as e:
            session_info["gemini"]["error"] = str(e)
            
        return session_info

    def open_interactive_login(self, service: str = "all"):
        """Opens a visible Firefox window with the persistent profile for manual authentication."""
        self.close()  # Close any headless session
        print(f"\n[BrowserController] Abriendo Firefox en modo visible para autenticación en {service.upper()}...")
        print(f"Perfil utilizado: {self.profile_dir}")
        print("Inicia sesión en tus cuentas de ChatGPT y/o Google Gemini.")
        print("Cuando hayas terminado, simplemente cierra la ventana de Firefox o presiona Enter aquí.\n")
        
        ctx = self.get_or_create_context(headless=False)
        if service.lower() in ["chatgpt", "all"]:
            p1 = ctx.new_page()
            p1.goto(CHATGPT_URL)
        if service.lower() in ["gemini", "all"]:
            p2 = ctx.new_page()
            p2.goto(GEMINI_URL)
            
        try:
            input("Presiona [ENTER] cuando hayas terminado de iniciar sesión para guardar el estado: ")
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.close()
            print("[BrowserController] Sesión y cookies persistentes guardadas en el perfil dedicado.")

    def close(self):
        """Cleanly closes context and playwright driver."""
        try:
            if self.context:
                self.context.close()
                self.context = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception:
            pass
