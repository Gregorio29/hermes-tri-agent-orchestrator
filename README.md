# Hermes Tri-Agent Orchestrator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Browser-Playwright%20Firefox-orange.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-5%20Passed-green.svg)](#)

An autonomous multi-agent coordination framework that orchestrates **ChatGPT** (tactical planner and reasoning engine), **Hermes** (local operating system sandbox executor), and **Gemini** (visual inspector and diagram designer) through structured JSON/text message protocols over persistent, isolated browser environments.

---

## 🤖 The Tri-Agent Architecture

```text
       ┌────────────────────────┐
       │     Mission Input      │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │        ChatGPT         │◀────────────────┐
       │ (Reasoning / Planning) │                 │
       └───────────┬────────────┘                 │
                   │                              │
                   ▼ (HERMES_ACTION)              │ (HERMES_RESULT)
       ┌────────────────────────┐                 │
       │     Hermes Executor    │─────────────────┘
       │ (System / CLI / Code)  │
       └───────────┬────────────┘
                   │
                   ▼ (Visual DOM Telemetry)
       ┌────────────────────────┐
       │     Gemini Visual      │
       │ (UI Layout / Diagrams) │
       └────────────────────────┘
```

---

## 🚀 Key Features

- **Decoupled Roles:** Specializes planning (ChatGPT), system execution (Hermes), and visual validation (Gemini).
- **Structured Protocol:** Uses a strictly typed `<HF_RESPONSE>` message envelope with validation for decisions, next actions, and expected outputs.
- **Loop Circuit Breaker:** Detects circular reasoning patterns and repetitive command deadlocks using sequence similarity algorithms and automatic rollbacks.
- **Gated Human Approvals:** Enforces interactive human confirmation for high-risk operations (`DELETE_CRITICAL_DATA`, `EXECUTE_PAYMENT`, `PUBLIC_PUBLISH`).
- **Complete Mission Telemetry:** Captures timestamps, stdout/stderr envelopes, screenshots, and conversation history in structured JSON artifacts.
- **Privacy Hardened:** Isolated from production browser profiles; zero hardcoded credentials or session cookies.

---

## 🛠️ Project Structure

```text
ChatGPTBridge/
├── bridges/                # Platform adapters (ChatGPT, Hermes, Gemini, Playwright)
├── core/                   # Protocol parser, loop controller, recovery manager
├── docs/                   # Protocol specification & system architecture
├── examples/               # Synthetic mission simulations
├── tests/                  # Unit tests for protocol serialization & safety breakers
├── cli.py                  # CLI mission orchestrator
├── config.py               # Environment-aware settings & timeouts
├── diagnostics.py          # Environment sanity & browser health checks
├── requirements.txt        # Runtime dependencies
└── LICENSE                 # MIT License
```

---

## 📦 Installation & Setup

```bash
git clone https://github.com/<username>/hermes-tri-agent-orchestrator.git
cd hermes-tri-agent-orchestrator
pip install -r requirements.txt
playwright install firefox
```

---

## 💻 CLI Usage

### Run a Mission
```bash
python cli.py run "Audit local repository, run unit tests, and summarize findings" --title "RepoAudit"
```

### Run Diagnostics
```bash
python diagnostics.py
```

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 Protocol Specification

See [`docs/protocol.md`](docs/protocol.md) for the complete Tri-Agent communication envelope format and lifecycle diagrams.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
