# Hermes Tri-Agent Orchestrator

[English](README.md) | [Español](README.es.md)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Browser-Playwright%20Firefox-orange.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-5%20Passed-green.svg)](#)

Un framework de coordinación multi-agente autónomo que orquesta a **ChatGPT** (planificador táctico y motor de razonamiento), **Hermes** (ejecutor en sandbox del sistema operativo local) y **Gemini** (auditor visual y diseñador de diagramas) mediante protocolos estructurados de mensajes JSON/texto sobre entornos aislados y persistentes de navegador.

---

## 🤖 Arquitectura Tri-Agent

```text
       ┌────────────────────────┐
       │   Objetivo de Misión   │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │        ChatGPT         │◀────────────────┐
       │ (Razonamiento / Plan)  │                 │
       └───────────┬────────────┘                 │
                   │                              │
                   ▼ (HERMES_ACTION)              │ (HERMES_RESULT)
       ┌────────────────────────┐                 │
       │    Ejecutor Hermes     │─────────────────┘
       │ (Sistema / CLI / Code) │
       └───────────┬────────────┘
                   │
                   ▼ (Telemetría Visual DOM)
       ┌────────────────────────┐
       │     Gemini Visual      │
       │ (Diseño UI / Diagramas)│
       └────────────────────────┘
```

---

## 🚀 Características Principales

- **Roles Desacoplados:** Especializa la planificación táctica (ChatGPT), la ejecución en el sistema operativo local (Hermes) y la validación visual de interfaces (Gemini).
- **Protocolo Estructurado:** Utiliza un sobre de mensajes estrictamente tipado `<HF_RESPONSE>` con validación de decisiones, siguientes acciones y resultados esperados.
- **Circuit Breaker de Bucles:** Detecta patrones de razonamiento circular y bloqueos repetitivos mediante algoritmos de similitud de cadenas y disparadores automáticos de rollback.
- **Autorización Humana Gated:** Obliga a una confirmación interactiva para acciones de alto riesgo (`DELETE_CRITICAL_DATA`, `EXECUTE_PAYMENT`, `PUBLIC_PUBLISH`).
- **Telemetría Completa de Misión:** Captura marcas de tiempo, sobres de stdout/stderr, capturas de pantalla y trazas de conversación en artefactos JSON estructurados.
- **Privacidad Endurecida:** Aislado de perfiles de producción del navegador; cero credenciales o cookies de sesión codificadas.

---

## 🛠️ Estructura del Proyecto

```text
ChatGPTBridge/
├── bridges/                # Adaptadores de plataforma (ChatGPT, Hermes, Gemini, Playwright)
├── core/                   # Parser de protocolo, loop controller, recovery manager
├── docs/                   # Especificación del protocolo y arquitectura del sistema
├── examples/               # Simulaciones sintéticas de misiones
├── tests/                  # Pruebas unitarias para serialización de protocolo y salvaguardas
├── cli.py                  # Orquestador CLI de misiones
├── config.py               # Configuración dependiente del entorno y timeouts
├── diagnostics.py          # Diagnóstico de entorno y comprobación de navegadores
├── requirements.txt        # Dependencias de ejecución
└── LICENSE                 # Licencia MIT
```

---

## 📦 Instalación y Configuración

```bash
git clone https://github.com/Gregorio29/hermes-tri-agent-orchestrator.git
cd hermes-tri-agent-orchestrator
pip install -r requirements.txt
playwright install firefox
```

---

## 💻 Uso desde la CLI

### Ejecutar una Misión
```bash
python cli.py run "Auditar repositorio local, ejecutar pruebas unitarias y resumir hallazgos" --title "RepoAudit"
```

### Ejecutar Diagnóstico de Entorno
```bash
python diagnostics.py
```

---

## 🧪 Ejecución de Pruebas Unitarias

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 Especificación del Protocolo

Consulta [`docs/protocol.md`](docs/protocol.md) para conocer el formato completo del sobre de comunicación Tri-Agent y los diagramas de ciclo de vida.

---

## 📄 Licencia

Este proyecto está distribuido bajo la [Licencia MIT](LICENSE).
