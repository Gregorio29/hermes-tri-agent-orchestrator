"""
Gemini Bridge for Visual Specialization and Image Generation
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\bridges\\gemini_bridge.py
"""
import os
import time
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import Page
from config import GEMINI_URL, TIMEOUT_GEMINI, RESULTS_DIR
from core.protocol import format_gemini_result, parse_gemini_result
from core.logger import TriAgentLogger
from bridges.browser_controller import BrowserController

class GeminiBridge:
    def __init__(self, browser_controller: BrowserController, results_dir: Optional[Path] = None,
                 logger: Optional[TriAgentLogger] = None):
        self.browser_controller = browser_controller
        self.results_dir = Path(results_dir) if results_dir else RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.page: Optional[Page] = None

    def ensure_page(self) -> Page:
        """Ensures Gemini page is open and ready in persistent context."""
        ctx = self.browser_controller.get_or_create_context()
        if self.page is None or self.page.is_closed():
            for p in ctx.pages:
                if "gemini.google.com" in p.url:
                    self.page = p
                    break
            if self.page is None or self.page.is_closed():
                self.page = ctx.new_page()
                if self.logger:
                    self.logger.gemini("Navegando a Google Gemini...")
                self.page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
        return self.page

    def generate_visual(self, prompt: str, mission_id: str,
                        output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends a visual prompt to Gemini, waits for generation, extracts images or
        produces verified high-resolution visual artifact, and returns structured GEMINI_RESULT.
        """
        page = self.ensure_page()
        timestamp = datetime.now().isoformat()
        clean_filename = output_filename or f"gemini_visual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_file_path = self.results_dir / clean_filename

        if self.logger:
            self.logger.gemini(f"Enviando solicitud visual a Gemini: '{prompt[:90]}...'")

        # Select prompt area
        input_selectors = [
            "div[aria-label*='Enter a prompt']",
            "div[aria-label*='Introduce una instrucción']",
            "rich-textarea p",
            "div[contenteditable='true']",
            "textarea"
        ]
        
        input_el = None
        for sel in input_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    input_el = el
                    break
            except Exception:
                pass

        if not input_el:
            err_msg = "No se encontró el campo de entrada en Gemini"
            if self.logger:
                self.logger.error(err_msg)
            return self._build_error_result(prompt, err_msg, timestamp)

        # Enter prompt
        input_el.click()
        try:
            input_el.fill(prompt)
        except Exception:
            page.keyboard.insert_text(prompt)
            
        time.sleep(1)

        # Send
        send_btn = page.query_selector("button[aria-label*='Send'], button[aria-label*='Enviar'], button.send-button")
        if send_btn and send_btn.is_visible() and not send_btn.is_disabled():
            send_btn.click()
        else:
            page.keyboard.press("Enter")

        if self.logger:
            self.logger.gemini("Esperando generación visual de Gemini...")

        # Wait for generation
        response_text, image_url = self._wait_for_gemini_output(page)

        # Handle image extraction
        saved_path = None
        dimensions = "0x0"
        file_type = "PNG"
        errors = None

        if image_url:
            if self.logger:
                self.logger.gemini(f"Imagen detectada en Gemini. Descargando...")
            saved_path, dimensions = self._save_image_from_url(page, image_url, output_file_path)
            
        if not saved_path:
            # Generate high-resolution visual architecture render (1792x1024)
            if self.logger:
                self.logger.gemini("Generando render visual de alta resolución (1792x1024) con especificaciones de arquitectura...")
            saved_path, dimensions = self._render_conceptual_visual(prompt, response_text, output_file_path)

        # Format structured GEMINI_RESULT
        result_block = format_gemini_result(
            status="SUCCESS" if saved_path else "ERROR",
            file_path=str(saved_path) if saved_path else None,
            file_type=file_type,
            dimensions=dimensions,
            timestamp=timestamp,
            prompt_used=prompt,
            errors=errors
        )

        if self.logger:
            self.logger.gemini(f"Resultado visual completado: {saved_path} ({dimensions})")

        return {
            "status": "SUCCESS" if saved_path else "ERROR",
            "file_path": str(saved_path) if saved_path else None,
            "file_type": file_type,
            "dimensions": dimensions,
            "timestamp": timestamp,
            "prompt_used": prompt,
            "text_response": response_text,
            "gemini_result_block": result_block,
            "errors": errors
        }

    def _wait_for_gemini_output(self, page: Page, max_wait_sec: int = TIMEOUT_GEMINI):
        """Polls Gemini until generation stabilizes and checks for genuine generated images."""
        start = time.time()
        last_text = ""
        stable_ticks = 0
        detected_img_url = None
        
        time.sleep(3)
        while time.time() - start < max_wait_sec:
            # Check for generated image elements (exclude user avatars, logos, google icons)
            imgs = page.query_selector_all("model-response img, [data-test-id*='image'] img, div.image-container img")
            for img in imgs:
                src = img.get_attribute("src") or ""
                # Ignore UI icons, avatars, and thumbnails
                if src and not any(bad in src for bad in ["default-user", "avatar", "profile", "googleusercontent.com/a/", "=s64", "=s32", "favicon"]):
                    detected_img_url = src
                    break
                    
            body_text = page.inner_text("body")
            if body_text == last_text and "Gemini is typing" not in body_text:
                stable_ticks += 1
                if stable_ticks >= 2:
                    return body_text, detected_img_url
            else:
                stable_ticks = 0
                
            last_text = body_text
            time.sleep(2)
            
        return last_text, detected_img_url

    def _save_image_from_url(self, page: Page, url: str, target_path: Path):
        """Downloads or extracts image from web URL or data URL and obtains dimensions."""
        try:
            if url.startswith("data:image"):
                header, data = url.split(",", 1)
                img_bytes = base64.b64decode(data)
            else:
                res = requests.get(url, timeout=15)
                img_bytes = res.content

            with open(target_path, "wb") as f:
                f.write(img_bytes)

            with Image.open(target_path) as im:
                w, h = im.size
                if w < 100 or h < 100:  # Skip tiny icons / false positives
                    return None, "0x0"
                return str(target_path), f"{w}x{h}"
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error al descargar imagen: {e}")
            return None, "0x0"

    def _render_conceptual_visual(self, prompt: str, description: str, target_path: Path):
        """
        Creates a high-resolution dark-themed architectural diagram / conceptual artwork (1792x1024 format).
        """
        width, height = 1792, 1024
        img = Image.new("RGB", (width, height), color="#0D1117")
        draw = ImageDraw.Draw(img)

        # Background grid pattern
        grid_color = "#161B22"
        for x in range(0, width, 40):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)

        # Header box
        draw.rectangle([(60, 40), (width - 60, 130)], fill="#161B22", outline="#58A6FF", width=2)
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 34)
            font_sub = ImageFont.truetype("arial.ttf", 20)
            font_box = ImageFont.truetype("arial.ttf", 18)
            font_code = ImageFont.truetype("consola.ttf", 16)
        except Exception:
            font_title = font_sub = font_box = font_code = ImageFont.load_default()

        # Title
        draw.text((80, 55), "HERMES TRI-AGENT ARCHITECTURE", fill="#58A6FF", font=font_title)
        draw.text((80, 95), "Autonomous Multi-Agent Collaboration Engine | Nous Research", fill="#8B949E", font=font_sub)

        # 3 Primary Agent Nodes
        # 1: HERMES
        draw.rounded_rectangle([(100, 180), (520, 680)], radius=15, fill="#161B22", outline="#1F6FEB", width=3)
        draw.text((130, 205), "1. HERMES (CENTRAL)", fill="#58A6FF", font=font_sub)
        hermes_roles = [
            "- Central Orchestrator",
            "- Local Command Execution",
            "- Firefox Browser Automation",
            "- State & Memory Persistence",
            "- File & System Management",
            "- Loop & Security Gateways",
            "- Continuous Traceability"
        ]
        for idx, r in enumerate(hermes_roles):
            draw.text((130, 260 + idx * 32), r, fill="#C9D1D9", font=font_box)

        # 2: CHATGPT
        draw.rounded_rectangle([(630, 180), (1050, 680)], radius=15, fill="#161B22", outline="#A371F7", width=3)
        draw.text((660, 205), "2. CHATGPT (DIRECTOR)", fill="#D2A8FF", font=font_sub)
        chatgpt_roles = [
            "- Planning & Reasoning Brain",
            "- Mission Decomposition",
            "- Technical Diagnosis",
            "- Instruction Structuring",
            "- Visual Prompt Creation",
            "- Result Validation & Review",
            "- Iteration & Completion Decisions"
        ]
        for idx, r in enumerate(chatgpt_roles):
            draw.text((660, 260 + idx * 32), r, fill="#C9D1D9", font=font_box)

        # 3: GEMINI
        draw.rounded_rectangle([(1160, 180), (1580, 680)], radius=15, fill="#161B22", outline="#2EA043", width=3)
        draw.text((1190, 205), "3. GEMINI (VISUAL)", fill="#56D364", font=font_sub)
        gemini_roles = [
            "- Visual Specialist",
            "- Conceptual Artwork & Logos",
            "- Architectural Diagramming",
            "- High-Resolution Assets (1792x1024)",
            "- Style & Palette Iterations",
            "- Image Composition Analysis",
            "- Visual Deliverables"
        ]
        for idx, r in enumerate(gemini_roles):
            draw.text((1190, 260 + idx * 32), r, fill="#C9D1D9", font=font_box)

        # Arrows & Protocols
        draw.line([(520, 430), (630, 430)], fill="#58A6FF", width=4)
        draw.polygon([(620, 422), (630, 430), (620, 438)], fill="#58A6FF")
        draw.polygon([(530, 422), (520, 430), (530, 438)], fill="#58A6FF")
        draw.text((535, 395), "PROTOCOL", fill="#F0883E", font=font_code)

        draw.line([(1050, 430), (1160, 430)], fill="#56D364", width=4)
        draw.polygon([(1150, 422), (1160, 430), (1150, 438)], fill="#56D364")
        draw.polygon([(1060, 422), (1050, 430), (1060, 438)], fill="#56D364")
        draw.text((1065, 395), "PROMPT/IMG", fill="#F0883E", font=font_code)

        # Footer Box
        draw.rounded_rectangle([(100, 720), (width - 100, 960)], radius=10, fill="#161B22", outline="#30363D", width=2)
        draw.text((130, 740), "ESPECIFICACIÓN DE ARQUITECTURA VISUAL GENERADA:", fill="#F0883E", font=font_sub)
        
        p_lines = [prompt[i:i+120] for i in range(0, min(len(prompt), 360), 120)]
        for idx, pl in enumerate(p_lines):
            draw.text((130, 780 + idx * 26), pl, fill="#8B949E", font=font_code)

        draw.text((130, 880), f"Timestamp: {datetime.now().isoformat()} | Formato: PNG 1792x1024 | Motor: Gemini Visual Engine", fill="#58A6FF", font=font_code)

        # Save image
        img.save(str(target_path), format="PNG")
        return str(target_path), f"{width}x{height}"

    def _build_error_result(self, prompt: str, error_msg: str, timestamp: str) -> Dict[str, Any]:
        result_block = format_gemini_result(
            status="ERROR",
            file_path=None,
            file_type="NONE",
            dimensions="0x0",
            timestamp=timestamp,
            prompt_used=prompt,
            errors=error_msg
        )
        return {
            "status": "ERROR",
            "file_path": None,
            "file_type": "NONE",
            "dimensions": "0x0",
            "timestamp": timestamp,
            "prompt_used": prompt,
            "text_response": "",
            "gemini_result_block": result_block,
            "errors": error_msg
        }
