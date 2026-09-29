# Hermes Tri-Agent Orchestrator — Architecture

## Overview
The Tri-Agent Orchestrator is a distributed multi-agent autonomous system combining three specialized foundation models into a unified execution feedback loop:

```text
                               ┌────────────────────────┐
                               │   Mission Controller   │
                               │        (cli.py)        │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │  Orchestrator Engine   │
                               │  (core/orchestrator.py)│
                               └───────────┬────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌───────────────────┐             ┌───────────────────┐             ┌───────────────────┐
│  ChatGPT Bridge   │             │   Hermes Bridge   │             │   Gemini Bridge   │
│ (Planning/Reason) │             │ (Local Execution) │             │ (Visual Analysis) │
│ - Firefox Web/API │             │ - Shell Execution │             │ - Firefox Web/API │
│ - Protocol Parser │             │ - File Inspection │             │ - Image Analysis  │
└───────────────────┘             └───────────────────┘             └───────────────────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │    Loop Controller     │
                               │ - Similarity Detector  │
                               │ - Circuit Breaker      │
                               │ - Recovery Manager     │
                               └────────────────────────┘
```

## Core Subsystems

1. **`bridges/`:** Platform adapters.
   - `chatgpt_bridge.py`: Manages reasoning turns, prompt injection, and response parsing over persistent web sessions.
   - `hermes_bridge.py`: Local OS sandbox driver executing filesystem operations and terminal subroutines.
   - `gemini_bridge.py`: Visual generator and screenshot inspector for DOM verification.
   - `browser_controller.py`: Playwright Firefox manager with profile isolation and stealth options.
2. **`core/`:** Orchestration mechanics.
   - `protocol.py`: Enforces `<HF_RESPONSE>` message envelope structure and error schemas.
   - `loop_controller.py`: Detects circular reasoning loops using string distance and entropy heuristics.
   - `recovery_manager.py`: Handles session re-attachments and exponential backoff on network dropouts.
   - `state_manager.py`: Records granular JSON mission traces and artifacts.
