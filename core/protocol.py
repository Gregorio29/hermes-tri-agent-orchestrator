"""
Agent Protocol and Structured Message Handling
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\protocol.py
"""
import re
from datetime import datetime
from typing import Dict, Any, Optional

CHATGPT_SYSTEM_PROMPT = """Eres el DIRECTOR TÉCNICO y CEREBRO DE PLANIFICACIÓN del sistema multi-agente HERMES TRI-AGENT ORCHESTRATOR.

AGENTES DEL SISTEMA:
1. HERMES: Orquestador y Ejecutor Local. Controla el ordenador, ejecuta scripts, comandos, inspecciona procesos y manipula archivos.
2. CHATGPT (TÚ): Cerebro de razonamiento, diagnóstico, descomposición de misiones, decisiones y revisión de resultados.
3. GEMINI: Especialista visual. Diseña y genera imágenes, diagramas conceptuales, piezas gráficas y material visual.

REGLAS DE COMUNICACIÓN OBLIGATORIAS:
Debes responder SIEMPRE utilizando la estructura estricta <HF_RESPONSE> ... </HF_RESPONSE>.

Estructura:
<HF_RESPONSE>
STATUS=CONTINUE|DONE|BLOCKED|NEEDS_USER|ERROR
AGENT=CHATGPT
TARGET_AGENT=HERMES|GEMINI|CHATGPT
TASK_SUMMARY:
<Breve resumen de la etapa actual o análisis>
NEXT_ACTION:
<Acción técnica concreta que Hermes debe ejecutar o delegar a Gemini>
PROMPT:
<Instrucción detallada para el TARGET_AGENT (ej. comando/script para Hermes o prompt visual descriptivo para Gemini)>
INPUT_REQUIRED:
YES|NO
OUTPUT_EXPECTED:
<Resultado esperado de la acción>
RETURN_REQUIRED:
YES|NO
</HF_RESPONSE>

PAUTAS DE DIRECCIÓN TÉCNICA:
- Si necesitas información del sistema o ejecutar código, asigna TARGET_AGENT=HERMES con el comando o script necesario.
- Si la misión requiere una imagen, ilustración o pieza gráfica, asigna TARGET_AGENT=GEMINI con un prompt visual rico y detallado en la sección PROMPT.
- Cuando recibas el resultado de Hermes o Gemini (incluyendo GEMINI_RESULT), revísalo críticamente. Si está correcto y se cumplió el objetivo de la misión, responde con STATUS=DONE. Si necesita corrección, solicita la siguiente iteración con STATUS=CONTINUE.
"""

def parse_hf_response(text: str) -> Dict[str, Any]:
    """
    Parses a <HF_RESPONSE> structured block from text.
    Fallback parser extracts fields even if formatting has slight variations.
    """
    response = {
        "raw_text": text,
        "is_valid": False,
        "status": "CONTINUE",
        "agent": "CHATGPT",
        "target_agent": "HERMES",
        "task_summary": "",
        "next_action": "",
        "prompt": "",
        "input_required": False,
        "output_expected": "",
        "return_required": True,
        "error": None
    }
    
    # Check if <HF_RESPONSE> tags exist
    tag_match = re.search(r"<HF_RESPONSE>(.*?)</HF_RESPONSE>", text, re.DOTALL | re.IGNORECASE)
    content = tag_match.group(1).strip() if tag_match else text.strip()
    
    # Extract STATUS
    m_status = re.search(r"STATUS\s*=\s*([A-Z_]+)", content, re.IGNORECASE)
    if m_status:
        val = m_status.group(1).upper()
        if val in ["CONTINUE", "DONE", "BLOCKED", "NEEDS_USER", "ERROR", "LOOP_DETECTED"]:
            response["status"] = val
            response["is_valid"] = True
            
    # Extract AGENT
    m_agent = re.search(r"^AGENT\s*=\s*([A-Z_]+)", content, re.IGNORECASE | re.MULTILINE)
    if m_agent:
        response["agent"] = m_agent.group(1).upper()
        
    # Extract TARGET_AGENT
    m_target = re.search(r"TARGET_AGENT\s*=\s*([A-Z_]+)", content, re.IGNORECASE)
    if m_target:
        val = m_target.group(1).upper()
        if val in ["HERMES", "GEMINI", "CHATGPT"]:
            response["target_agent"] = val
            
    # Helper to extract multi-line fields between headers
    headers = [
        ("TASK_SUMMARY", "task_summary"),
        ("NEXT_ACTION", "next_action"),
        ("PROMPT", "prompt"),
        ("INPUT_REQUIRED", "input_required"),
        ("OUTPUT_EXPECTED", "output_expected"),
        ("RETURN_REQUIRED", "return_required")
    ]
    
    for h_name, field_key in headers:
        # Regex to capture content following HEADER:\n up to next header or end
        pattern = rf"{h_name}\s*:\s*\n?(.*?)(?=(?:TASK_SUMMARY|NEXT_ACTION|TARGET_AGENT|PROMPT|INPUT_REQUIRED|OUTPUT_EXPECTED|RETURN_REQUIRED|STATUS|AGENT)\s*[:=]|$)"
        m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if field_key in ["input_required", "return_required"]:
                response[field_key] = True if "YES" in val.upper() or "TRUE" in val.upper() else False
            else:
                response[field_key] = val

    # Fallback if unformatted text was returned but contains meaningful instructions
    if not response["is_valid"]:
        # If ChatGPT simply answered conversationally, package it
        response["task_summary"] = "Respuesta textual de ChatGPT"
        response["next_action"] = "Procesar respuesta de ChatGPT"
        response["prompt"] = text.strip()
        response["is_valid"] = True
        
    return response


def format_hf_response(status: str, agent: str, target_agent: str,
                       task_summary: str, next_action: str, prompt: str,
                       input_required: bool = False, output_expected: str = "",
                       return_required: bool = True) -> str:
    """Formats a dictionary/fields into a valid <HF_RESPONSE> string."""
    return f"""<HF_RESPONSE>
STATUS={status.upper()}
AGENT={agent.upper()}
TARGET_AGENT={target_agent.upper()}

TASK_SUMMARY:
{task_summary}

NEXT_ACTION:
{next_action}

PROMPT:
{prompt}

INPUT_REQUIRED:
{"YES" if input_required else "NO"}

OUTPUT_EXPECTED:
{output_expected}

RETURN_REQUIRED:
{"YES" if return_required else "NO"}
</HF_RESPONSE>"""


def format_gemini_result(status: str, file_path: Optional[str], file_type: str,
                         dimensions: str, timestamp: str, prompt_used: str,
                         errors: Optional[str] = None) -> str:
    """Formats the standardized GEMINI_RESULT report block."""
    return f"""GEMINI_RESULT:
STATUS={status.upper()}
FILE_PATH={file_path or 'NONE'}
FILE_TYPE={file_type}
DIMENSIONS={dimensions}
TIMESTAMP={timestamp}
PROMPT_USED={prompt_used}
ERRORS={errors or 'NONE'}"""


def parse_gemini_result(text: str) -> Dict[str, Any]:
    """Parses a GEMINI_RESULT string into structured data."""
    res = {
        "status": "ERROR",
        "file_path": None,
        "file_type": "UNKNOWN",
        "dimensions": "0x0",
        "timestamp": "",
        "prompt_used": "",
        "errors": None
    }
    for line in text.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip().upper()
            v = v.strip()
            if k == "STATUS":
                res["status"] = v
            elif k == "FILE_PATH":
                res["file_path"] = None if v == "NONE" else v
            elif k == "FILE_TYPE":
                res["file_type"] = v
            elif k == "DIMENSIONS":
                res["dimensions"] = v
            elif k == "TIMESTAMP":
                res["timestamp"] = v
            elif k == "PROMPT_USED":
                res["prompt_used"] = v
            elif k == "ERRORS":
                res["errors"] = None if v == "NONE" else v
    return res


def format_action_envelope(action_id: str, mission_id: str, agent: str,
                           timestamp: str, input_data: Any, output_data: Any,
                           status: str, error: Optional[str] = None) -> Dict[str, Any]:
    """Creates a standardized action trace dictionary."""
    return {
        "action_id": action_id,
        "mission_id": mission_id,
        "agent": agent.upper(),
        "timestamp": timestamp or datetime.now().isoformat(),
        "input": input_data,
        "output": output_data,
        "status": status.upper(),
        "error": error
    }
