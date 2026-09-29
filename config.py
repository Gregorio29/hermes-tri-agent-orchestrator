"""
Configuration settings for Hermes Tri-Agent Orchestrator
Modular, environment-aware configuration with dynamic base paths.
"""
import os
from pathlib import Path

# Base Paths dynamically resolved
BASE_DIR = Path(os.environ.get("CHATGPT_BRIDGE_HOME", Path(__file__).resolve().parent))
STATE_DIR = BASE_DIR / "state"
MISSIONS_DIR = BASE_DIR / "missions"
PROFILES_DIR = BASE_DIR / "profiles"
FIREFOX_PROFILE_DIR = PROFILES_DIR / "firefox_agent_profile"
RESULTS_DIR = BASE_DIR / "results"
DOCS_DIR = BASE_DIR / "docs"

# Ensure core directories exist
for p in [STATE_DIR, MISSIONS_DIR, PROFILES_DIR, RESULTS_DIR, DOCS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# System and Loop Controls
MAX_ITERATIONS = int(os.environ.get("BRIDGE_MAX_ITERATIONS", "100"))
MAX_RETRIES = int(os.environ.get("BRIDGE_MAX_RETRIES", "3"))
LOOP_DETECTION_WINDOW = int(os.environ.get("BRIDGE_LOOP_WINDOW", "5"))
SIMILARITY_THRESHOLD = float(os.environ.get("BRIDGE_SIMILARITY_THRESHOLD", "0.95"))

# Timeouts (seconds)
TIMEOUT_CHATGPT = int(os.environ.get("TIMEOUT_CHATGPT", "120"))
TIMEOUT_GEMINI = int(os.environ.get("TIMEOUT_GEMINI", "120"))
TIMEOUT_HERMES = int(os.environ.get("TIMEOUT_HERMES", "60"))
BROWSER_PAGE_TIMEOUT = int(os.environ.get("BROWSER_PAGE_TIMEOUT", "30000"))  # ms for playwright

# Browser Settings
FIREFOX_HEADLESS = os.environ.get("FIREFOX_HEADLESS", "true").lower() in ["true", "1", "yes"]
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
)

# URLs
CHATGPT_URL = os.environ.get("CHATGPT_URL", "https://chatgpt.com")
GEMINI_URL = os.environ.get("GEMINI_URL", "https://gemini.google.com/app")

# Human Approval Safeguards (Gated execution)
REQUIRE_HUMAN_APPROVAL_ACTIONS = [
    "DELETE_CRITICAL_DATA",
    "EXECUTE_PAYMENT",
    "PUBLIC_PUBLISH",
    "MODIFY_SYSTEM_REGISTRY",
    "DESTRUCTIVE_FILE_OVERWRITE"
]
