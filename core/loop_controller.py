"""
Loop Controller and Safeguards
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\loop_controller.py
"""
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple, Optional
from config import MAX_ITERATIONS, MAX_RETRIES, LOOP_DETECTION_WINDOW, SIMILARITY_THRESHOLD

class LoopController:
    def __init__(self, max_iterations: int = MAX_ITERATIONS, max_retries: int = MAX_RETRIES):
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}
        self.prompt_history: List[str] = []
        self.action_history: List[Dict[str, Any]] = []
        self.response_history: List[str] = []

    def _calculate_similarity(self, a: str, b: str) -> float:
        """Computes similarity ratio between two strings."""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

    def check_iteration_limit(self, current_iteration: int) -> Tuple[bool, Optional[str]]:
        """Verifies if global iteration ceiling is reached."""
        if current_iteration >= self.max_iterations:
            return True, f"Límite máximo de iteraciones alcanzado ({self.max_iterations})"
        return False, None

    def record_and_check_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Checks if identical or highly similar prompt is repeatedly sent."""
        clean_prompt = prompt.strip()
        self.prompt_history.append(clean_prompt)
        
        # Check against recent window
        recent = self.prompt_history[-LOOP_DETECTION_WINDOW:]
        if len(recent) >= 3:
            # Check 3 identical consecutive prompts
            if recent[-1] == recent[-2] == recent[-3]:
                return True, "Detección de bucle: Mismo prompt enviado 3 veces consecutivas"
            
            # Check similarity ratio
            sim1 = self._calculate_similarity(recent[-1], recent[-2])
            sim2 = self._calculate_similarity(recent[-2], recent[-3])
            if sim1 > SIMILARITY_THRESHOLD and sim2 > SIMILARITY_THRESHOLD:
                return True, f"Detección de bucle: Variación mínima en prompts consecutivos (> {SIMILARITY_THRESHOLD*100}%)"
                
        return False, None

    def record_and_check_action(self, agent: str, action_type: str, action_input: Any) -> Tuple[bool, Optional[str]]:
        """Checks if identical action is repeated without progress."""
        entry = {
            "agent": agent,
            "action_type": action_type,
            "input": str(action_input)
        }
        self.action_history.append(entry)
        
        recent = self.action_history[-LOOP_DETECTION_WINDOW:]
        if len(recent) >= 3:
            if (recent[-1]["agent"] == recent[-2]["agent"] == recent[-3]["agent"] and
                recent[-1]["input"] == recent[-2]["input"] == recent[-3]["input"]):
                return True, f"Detección de bucle: Acción idéntica de {agent} repetida 3 veces"
                
        return False, None

    def record_and_check_response(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """Checks if agent responses are completely identical / stuck."""
        clean_res = response_text.strip()
        self.response_history.append(clean_res)
        
        recent = self.response_history[-LOOP_DETECTION_WINDOW:]
        if len(recent) >= 3:
            if recent[-1] == recent[-2] == recent[-3] and len(recent[-1]) > 10:
                return True, "Detección de bucle: Respuestas idénticas recibidas consecutivamente"
        return False, None

    def record_error(self, error_key: str) -> Tuple[bool, int]:
        """Tracks error repetition for a specific key/operation."""
        self.retry_counts[error_key] = self.retry_counts.get(error_key, 0) + 1
        count = self.retry_counts[error_key]
        exceeded = count > self.max_retries
        return exceeded, count

    def reset_error(self, error_key: str):
        """Clears error counter upon successful execution."""
        if error_key in self.retry_counts:
            del self.retry_counts[error_key]
