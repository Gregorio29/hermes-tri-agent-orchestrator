"""
System Diagnostics and Environment Audit
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\diagnostics.py
"""
import os
import sys
import json
from pathlib import Path
from config import BASE_DIR, FIREFOX_PROFILE_DIR, STATE_DIR
from bridges.browser_controller import BrowserController
from core.logger import default_logger

def run_diagnostics(check_web_sessions: bool = True) -> dict:
    """Runs a full system diagnostic audit."""
    print("=" * 70)
    print("  HERMES TRI-AGENT ORCHESTRATOR - DIAGNÓSTICO DEL SISTEMA")
    print("=" * 70)

    results = {
        "base_directory": str(BASE_DIR),
        "base_dir_exists": BASE_DIR.exists(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "subsystems": {}
    }

    # 1. Check directories
    dirs_status = {}
    for d in ["core", "bridges", "state", "missions", "profiles", "results", "docs"]:
        p = BASE_DIR / d
        dirs_status[d] = {"path": str(p), "exists": p.exists()}
    results["directories"] = dirs_status

    # 2. Browser Controller & Firefox Audit
    browser_ctrl = BrowserController(profile_dir=FIREFOX_PROFILE_DIR)
    env_audit = browser_ctrl.audit_environment()
    results["environment"] = env_audit

    # 3. Web Sessions Check (Optional fast vs full)
    if check_web_sessions:
        print("[*] Comprobando sesiones web en ChatGPT y Gemini (Firefox)...")
        session_info = browser_ctrl.detect_sessions()
        results["sessions"] = session_info
        browser_ctrl.close()
    else:
        results["sessions"] = "Skipped"

    # Display clean report
    print(f"\n[+] Directorio Base: {BASE_DIR} ({'OK' if BASE_DIR.exists() else 'ERROR'})")
    print(f"[+] Python: {results['python_version']} ({results['python_executable']})")
    print(f"[+] Firefox Instalado: {env_audit['firefox_installed']}")
    if env_audit["firefox_paths"]:
        for fp in env_audit["firefox_paths"]:
            print(f"    - Ruta: {fp}")
    print(f"[+] Perfiles Firefox en Sistema: {len(env_audit['firefox_profiles'])}")
    print(f"[+] Perfil Dedicado Automatización: {env_audit['dedicated_profile_path']}")
    print(f"[+] Playwright Firefox Driver: {env_audit.get('playwright_firefox_driver')} (v{env_audit.get('firefox_driver_version', 'N/A')})")
    print(f"[+] Node.js: {'Disponible (' + env_audit['node_version'] + ')' if env_audit['node_available'] else 'No encontrado'}")

    if check_web_sessions and isinstance(results.get("sessions"), dict):
        cg = results["sessions"].get("chatgpt", {})
        gem = results["sessions"].get("gemini", {})
        print("\n--- ESTADO DE SESIONES WEB ---")
        print(f"[*] ChatGPT: Accesible={cg.get('accessible')}, Autenticado={cg.get('authenticated')}, Modo={cg.get('mode')}")
        print(f"[*] Gemini:  Accesible={gem.get('accessible')}, Autenticado={gem.get('authenticated')}, Modo={gem.get('mode')}")

    print("\n" + "=" * 70)
    print("  DIAGNÓSTICO COMPLETADO")
    print("=" * 70 + "\n")
    return results

if __name__ == "__main__":
    check_web = "--no-web" not in sys.argv
    run_diagnostics(check_web_sessions=check_web)
