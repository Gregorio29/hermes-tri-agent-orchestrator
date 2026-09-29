"""
ChatGPT Bridge for Web Automation via Firefox
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\bridges\\chatgpt_bridge.py
"""
import time
from typing import Dict, Any, Optional
from playwright.sync_api import Page, BrowserContext
from config import CHATGPT_URL, TIMEOUT_CHATGPT
from core.protocol import parse_hf_response, CHATGPT_SYSTEM_PROMPT
from core.logger import TriAgentLogger
from bridges.browser_controller import BrowserController

class ChatGPTBridge:
    def __init__(self, browser_controller: BrowserController, logger: Optional[TriAgentLogger] = None):
        self.browser_controller = browser_controller
        self.logger = logger
        self.page: Optional[Page] = None
        self.is_initialized = False

    def ensure_page(self) -> Page:
        """Ensures ChatGPT page is open and ready."""
        ctx = self.browser_controller.get_or_create_context()
        if self.page is None or self.page.is_closed():
            # Check if there's already a chatgpt tab
            for p in ctx.pages:
                if "chatgpt.com" in p.url:
                    self.page = p
                    break
            if self.page is None or self.page.is_closed():
                self.page = ctx.new_page()
                if self.logger:
                    self.logger.chatgpt("Navegando a ChatGPT...")
                self.page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
        return self.page

    def send_prompt(self, user_prompt: str, is_first_turn: bool = False) -> Dict[str, Any]:
        """
        Sends a prompt to ChatGPT and waits for the complete response.
        """
        page = self.ensure_page()
        
        # Format payload: on first turn, ensure system instructions are communicated
        full_prompt = user_prompt
        if is_first_turn and not self.is_initialized:
            full_prompt = f"{CHATGPT_SYSTEM_PROMPT}\n\n--- INICIO DE MISIÓN ---\n{user_prompt}"
            self.is_initialized = True

        if self.logger:
            self.logger.chatgpt(f"Enviando mensaje ({len(full_prompt)} caracteres)...")

        # Find prompt input
        selectors = [
            "#prompt-textarea",
            "#mobile-composer-prompt",
            "div[contenteditable='true']",
            "textarea[placeholder*='Ask']",
            "textarea"
        ]
        
        input_el = None
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    input_el = el
                    break
            except Exception:
                pass

        if not input_el:
            err_msg = "No se encontró el campo de entrada de texto en ChatGPT"
            if self.logger:
                self.logger.error(err_msg)
            return {"status": "ERROR", "error": err_msg, "parsed": parse_hf_response(err_msg)}

        # Focus and fill text
        try:
            input_el.click()
            # If standard fill works:
            input_el.fill(full_prompt)
        except Exception:
            # Fallback using clipboard/keyboard
            input_el.click()
            page.keyboard.insert_text(full_prompt)

        time.sleep(1)

        # Click send button
        send_selectors = [
            "button[data-testid='send-button']",
            "button[data-testid='fruitjuice-send-button']",
            "button[aria-label*='Send']",
            "button[aria-label*='Enviar']"
        ]
        
        sent = False
        for s_sel in send_selectors:
            btn = page.query_selector(s_sel)
            if btn and btn.is_visible() and not btn.is_disabled():
                btn.click()
                sent = True
                break
                
        if not sent:
            page.keyboard.press("Enter")

        if self.logger:
            self.logger.chatgpt("Mensaje enviado. Esperando respuesta estructurada...")

        # Wait for generation to complete
        response_text = self._wait_for_response(page)
        
        if not response_text:
            err_msg = "Tiempo de espera agotado o respuesta vacía de ChatGPT"
            if self.logger:
                self.logger.error(err_msg)
            return {"status": "ERROR", "error": err_msg, "parsed": parse_hf_response(err_msg)}

        parsed = parse_hf_response(response_text)
        if self.logger:
            self.logger.chatgpt(f"Respuesta recibida [STATUS={parsed['status']}, TARGET={parsed['target_agent']}]")
            
        return {
            "status": "SUCCESS",
            "raw_text": response_text,
            "parsed": parsed
        }

    def _wait_for_response(self, page: Page, max_wait_sec: int = TIMEOUT_CHATGPT) -> str:
        """Polls until ChatGPT finishes streaming the response and stabilizes."""
        start_time = time.time()
        last_text = ""
        stable_count = 0
        
        # Initial grace period for generation to start
        time.sleep(3)
        
        while time.time() - start_time < max_wait_sec:
            current_text = self._extract_latest_response(page)
            
            # Check if stop button is active
            stop_btn = page.query_selector("button[aria-label*='Stop'], button[data-testid='stop-button']")
            is_generating = stop_btn and stop_btn.is_visible()
            
            if current_text and current_text == last_text and not is_generating:
                stable_count += 1
                if stable_count >= 2:  # Text remained unchanged for 2 consecutive checks
                    return current_text
            else:
                stable_count = 0
                
            last_text = current_text
            time.sleep(2)
            
        return last_text

    def _extract_latest_response(self, page: Page) -> str:
        """Extracts the latest response from ChatGPT DOM."""
        try:
            # First try structured role containers
            assistants = page.query_selector_all("[data-message-author-role='assistant'], div.markdown")
            if assistants:
                return assistants[-1].inner_text().strip()
                
            # Fallback: inspect full body text splitting by ChatGPT said / markers
            body_text = page.inner_text("body")
            if "ChatGPT said:" in body_text:
                parts = body_text.split("ChatGPT said:")
                last_part = parts[-1]
                # Strip trailing UI text if present
                for end_marker in ["Chat with ChatGPT", "Ask a follow up", "Log in to get answers"]:
                    if end_marker in last_part:
                        last_part = last_part.split(end_marker)[0]
                return last_part.strip()
                
            return ""
        except Exception as e:
            return ""
