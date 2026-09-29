# Hermes Tri-Agent Protocol Specification (v1.0)

## 1. Overview
The Tri-Agent Protocol is a structured asynchronous inter-agent communication specification that coordinates three specialized AI instances across a distributed mission lifecycle:

1. **ChatGPT (Planner / Reasoner):** Breaks complex directives into discrete, verified multi-step tactical action plans.
2. **Hermes (Local Executor):** Performs sandboxed system actions (filesystem operations, CLI executions, code patches, network queries).
3. **Gemini (Visual & DOM Auditor):** Inspects visual screenshots, spatial DOM hierarchy, rendered canvas/UI artifacts, and OCR telemetry.

```text
       ┌────────────────────────┐
       │   USER / ORCHESTRATOR  │
       └───────────┬────────────┘
                   │
                   ▼ (1) Mission Objective
       ┌────────────────────────┐
       │        ChatGPT         │◀────────────────┐
       │   (Planner/Reasoner)   │                 │
       └───────────┬────────────┘                 │
                   │                              │
                   ▼ (2) ACTION_BLOCK             │ (5) RESULT_BLOCK
       ┌────────────────────────┐                 │
       │    Hermes Executor     │─────────────────┘
       │  (System & File Tool)  │
       └───────────┬────────────┘
                   │
                   ▼ (3) Visual Trigger / Screenshot
       ┌────────────────────────┐
       │      Gemini Visual     │
       │  (Layout & DOM Auditor)│
       └────────────────────────┘
```

---

## 2. Message Envelope & Protocol Blocks

### 2.1 ChatGPT Action Directives (`[HERMES_ACTION]`)
ChatGPT issues commands to Hermes using formatted, unambiguous blocks:

```text
[HERMES_ACTION]
ACTION_ID=ACT-00042
TYPE=TERMINAL_COMMAND
COMMAND=pytest -v tests/
TIMEOUT=60
ON_FAILURE=RETRY_WITH_MODIFIED_PAYLOAD
[/HERMES_ACTION]
```

### 2.2 Hermes Execution Results (`[HERMES_RESULT]`)
Hermes feeds the exact stdout, stderr, and exit codes back to the Planner:

```text
[HERMES_RESULT]
ACTION_ID=ACT-00042
STATUS=SUCCESS
EXIT_CODE=0
OUTPUT:
======================= 4 passed in 0.12s =======================
[/HERMES_RESULT]
```

### 2.3 Gemini Visual Audit Queries (`[GEMINI_AUDIT]`)
When spatial or visual verification is needed, Gemini analyzes rendered state:

```text
[GEMINI_AUDIT]
QUERY=Verify that the submit button on the login form is rendered in green and is not obscured.
IMAGE_REF=results/gemini_visual_20260928_220000.png
[/GEMINI_AUDIT]
```

---

## 3. Loop Detection & Safety Circuit Breakers

1. **Loop Detection Window:** Tracks the similarity index of the last 5 action payloads using Levenshtein distance and token entropy. If similarity exceeds `0.95`, the loop controller triggers an automatic rollback or re-planning interrupt.
2. **Gated Human Approvals:** Any destructive operation (`DELETE_CRITICAL_DATA`, `EXECUTE_PAYMENT`, `PUBLIC_PUBLISH`) halts the execution loop until an explicit human authorization token is provided.
