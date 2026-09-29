"""
CLI Interface for Hermes Tri-Agent Orchestrator
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\cli.py
"""
import sys
import argparse
import json
from pathlib import Path

# Add base directory to python path
BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import MISSIONS_DIR, STATE_DIR
from core.mission_manager import MissionManager
from core.orchestrator import TriAgentOrchestrator
from core.logger import default_logger
from bridges.browser_controller import BrowserController
from diagnostics import run_diagnostics

def cmd_run(args):
    """Starts a new mission."""
    title = args.title or (args.instruction[:30] + "..." if len(args.instruction) > 30 else args.instruction)
    instruction = args.instruction
    
    mgr = MissionManager()
    state_mgr = mgr.create_mission(title=title, description=instruction)
    
    orchestrator = TriAgentOrchestrator(state_manager=state_mgr)
    print(f"\n[+] Iniciando Misión ID: {state_mgr.mission_id}")
    print(f"[+] Título: {title}")
    print(f"[+] Instrucción: {instruction}\n")
    orchestrator.run_mission(initial_instruction=instruction)

def cmd_resume(args):
    """Resumes an existing or latest mission."""
    mgr = MissionManager()
    if args.mission_id:
        state_mgr = mgr.load_mission(args.mission_id)
        if not state_mgr:
            print(f"[-] Error: Misión '{args.mission_id}' no encontrada.")
            return
    else:
        state_mgr = mgr.get_latest_mission()
        if not state_mgr:
            print("[-] No se encontraron misiones para reanudar.")
            return

    print(f"\n[+] Reanudando Misión: {state_mgr.mission_id} (Estado: {state_mgr.mission_data.get('status')})")
    orchestrator = TriAgentOrchestrator(state_manager=state_mgr)
    orchestrator.run_mission()

def cmd_list(args):
    """Lists all missions."""
    mgr = MissionManager()
    missions = mgr.list_missions()
    print("\n" + "=" * 80)
    print(f"  REGISTRO DE MISIONES ({len(missions)} encontradas)")
    print("=" * 80)
    if not missions:
        print("  (No hay misiones registradas aún)")
    for m in missions:
        m_id = m.get("mission_id")
        title = m.get("title", "Sin título")
        status = m.get("status", "UNKNOWN")
        iter_count = m.get("current_iteration", 0)
        created = m.get("created_at", "")[:19]
        print(f"• [{status:<10}] {m_id:<28} | Iter: {iter_count:<3} | Creado: {created} | {title}")
    print("=" * 80 + "\n")

def cmd_status(args):
    """Shows full status of a mission."""
    mgr = MissionManager()
    if args.mission_id:
        state_mgr = mgr.load_mission(args.mission_id)
    else:
        state_mgr = mgr.get_latest_mission()
        
    if not state_mgr:
        print("[-] No se encontró información de misión.")
        return
        
    data = state_mgr.mission_data
    print("\n" + "=" * 70)
    print(f"  ESTADO DE MISIÓN: {data.get('mission_id')}")
    print("=" * 70)
    print(f"Título:            {data.get('title')}")
    print(f"Estado:            {data.get('status')}")
    print(f"Iteración Actual:  {data.get('current_iteration')}")
    print(f"Agente Actual:     {data.get('current_agent')}")
    print(f"Próximo Objetivo:  {data.get('next_target_agent')}")
    print(f"Creado:            {data.get('created_at')}")
    print(f"Actualizado:       {data.get('updated_at')}")
    print("\n--- Estadísticas ---")
    for k, v in data.get("stats", {}).items():
        print(f"  {k}: {v}")
    print(f"\nTotal Acciones Registradas: {len(state_mgr.actions)}")
    print(f"Total Artefactos Creados:   {len(state_mgr.artifacts)}")
    if state_mgr.artifacts:
        print("\n--- Artefactos ---")
        for art in state_mgr.artifacts:
            print(f"  [{art.get('file_type')}] {art.get('filename')} ({art.get('dimensions')}) -> {art.get('file_path')}")
    print("=" * 70 + "\n")

def cmd_login(args):
    """Opens visible browser for login."""
    b_ctrl = BrowserController()
    b_ctrl.open_interactive_login(service=args.service)

def cmd_diagnostics(args):
    """Runs diagnostics."""
    run_diagnostics(check_web_sessions=not args.no_web)

def cmd_test(args):
    """Runs the required 3-agent orchestration test."""
    mission_text = (
        "Analiza el entorno actual de Hermes, prepara una pequeña propuesta visual "
        "sobre la arquitectura del sistema y genera una imagen conceptual utilizando Gemini."
    )
    print("\n[+] Ejecutando prueba de integración de 3 agentes (HERMES, CHATGPT, GEMINI)...")
    mgr = MissionManager()
    state_mgr = mgr.create_mission(
        title="Prueba Tri-Agent Arquitectura",
        description=mission_text
    )
    orchestrator = TriAgentOrchestrator(state_manager=state_mgr)
    orchestrator.run_mission(initial_instruction=mission_text)

def main():
    parser = argparse.ArgumentParser(
        description="Hermes Tri-Agent Orchestrator CLI (Hermes + ChatGPT + Gemini)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # run
    p_run = subparsers.add_parser("run", help="Iniciar una nueva misión")
    p_run.add_argument("instruction", type=str, help="Descripción o instrucción de la misión")
    p_run.add_argument("--title", type=str, default=None, help="Título corto opcional")

    # resume
    p_resume = subparsers.add_parser("resume", help="Reanudar una misión existente")
    p_resume.add_argument("mission_id", nargs="?", default=None, help="ID de la misión a reanudar")

    # list
    subparsers.add_parser("list", help="Listar todas las misiones registradas")

    # status
    p_status = subparsers.add_parser("status", help="Ver estado detallado de una misión")
    p_status.add_argument("mission_id", nargs="?", default=None, help="ID de la misión")

    # login
    p_login = subparsers.add_parser("login", help="Abrir Firefox en modo visible para iniciar sesión")
    p_login.add_argument("--service", choices=["chatgpt", "gemini", "all"], default="all", help="Servicio a autenticar")

    # diagnostics / doctor
    p_diag = subparsers.add_parser("doctor", help="Verificar estado de herramientas y entorno")
    p_diag.add_argument("--no-web", action="store_true", help="Omitir verificación web de sesiones")
    p_diag_alias = subparsers.add_parser("diagnostics", help="Alias para doctor")
    p_diag_alias.add_argument("--no-web", action="store_true", help="Omitir verificación web de sesiones")

    # test
    subparsers.add_parser("test", help="Ejecutar prueba de validación con los 3 agentes")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "resume":
        cmd_resume(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "login":
        cmd_login(args)
    elif args.command in ["doctor", "diagnostics"]:
        cmd_diagnostics(args)
    elif args.command == "test":
        cmd_test(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
