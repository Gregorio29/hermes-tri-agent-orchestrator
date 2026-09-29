"""
Central State Manager for Shared Memory and Mission Persistence
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\state_manager.py
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import BASE_DIR, STATE_DIR, MISSIONS_DIR

class StateManager:
    def __init__(self, mission_id: Optional[str] = None):
        self.mission_id = mission_id or f"MIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.mission_dir = MISSIONS_DIR / self.mission_id
        self.results_dir = self.mission_dir / "results"
        self.screenshots_dir = self.mission_dir / "screenshots"
        
        # Ensure mission specific directories
        self.mission_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths for the required 6 core state files
        self.files = {
            "mission": self.mission_dir / "mission.json",
            "conversation_chatgpt": self.mission_dir / "conversation_chatgpt.json",
            "conversation_gemini": self.mission_dir / "conversation_gemini.json",
            "actions": self.mission_dir / "actions.json",
            "artifacts": self.mission_dir / "artifacts.json",
            "events": self.mission_dir / "events.log"
        }
        
        # In-memory structures
        self.mission_data: Dict[str, Any] = {}
        self.conversation_chatgpt: List[Dict[str, Any]] = []
        self.conversation_gemini: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        
        # Load or initialize
        if self.files["mission"].exists():
            self._load_state()
        else:
            self._init_empty_state()

    def _init_empty_state(self):
        """Initializes empty structures for a new mission."""
        now = datetime.now().isoformat()
        self.mission_data = {
            "mission_id": self.mission_id,
            "title": "Nueva Misión",
            "description": "",
            "created_at": now,
            "updated_at": now,
            "status": "INITIALIZED",  # INITIALIZED, RUNNING, PAUSED, BLOCKED, DONE, ERROR, LOOP_DETECTED
            "current_iteration": 0,
            "current_agent": "HERMES",
            "next_target_agent": "CHATGPT",
            "stats": {
                "chatgpt_turns": 0,
                "gemini_turns": 0,
                "hermes_actions": 0,
                "total_errors": 0
            }
        }
        self.conversation_chatgpt = []
        self.conversation_gemini = []
        self.actions = []
        self.artifacts = []
        self.save_all()

    def _load_state(self):
        """Loads state files from mission directory."""
        try:
            if self.files["mission"].exists():
                with open(self.files["mission"], "r", encoding="utf-8") as f:
                    self.mission_data = json.load(f)
            if self.files["conversation_chatgpt"].exists():
                with open(self.files["conversation_chatgpt"], "r", encoding="utf-8") as f:
                    self.conversation_chatgpt = json.load(f)
            if self.files["conversation_gemini"].exists():
                with open(self.files["conversation_gemini"], "r", encoding="utf-8") as f:
                    self.conversation_gemini = json.load(f)
            if self.files["actions"].exists():
                with open(self.files["actions"], "r", encoding="utf-8") as f:
                    self.actions = json.load(f)
            if self.files["artifacts"].exists():
                with open(self.files["artifacts"], "r", encoding="utf-8") as f:
                    self.artifacts = json.load(f)
        except Exception as e:
            print(f"[StateManager] Error loading state for {self.mission_id}: {e}")

    def save_all(self):
        """Persists all state files to disk and mirrors to shared state/ directory."""
        self.mission_data["updated_at"] = datetime.now().isoformat()
        
        # Save to mission directory
        self._write_json(self.files["mission"], self.mission_data)
        self._write_json(self.files["conversation_chatgpt"], self.conversation_chatgpt)
        self._write_json(self.files["conversation_gemini"], self.conversation_gemini)
        self._write_json(self.files["actions"], self.actions)
        self._write_json(self.files["artifacts"], self.artifacts)
        
        # Mirror to global state/ directory for active mission observation
        try:
            self._write_json(STATE_DIR / "mission.json", self.mission_data)
            self._write_json(STATE_DIR / "conversation_chatgpt.json", self.conversation_chatgpt)
            self._write_json(STATE_DIR / "conversation_gemini.json", self.conversation_gemini)
            self._write_json(STATE_DIR / "actions.json", self.actions)
            self._write_json(STATE_DIR / "artifacts.json", self.artifacts)
            if self.files["events"].exists():
                shutil.copy2(self.files["events"], STATE_DIR / "events.log")
        except Exception as e:
            pass

    def _write_json(self, path: Path, data: Any):
        """Atomic write JSON file."""
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(str(tmp_path), str(path))

    def record_action(self, agent: str, input_data: Any, output_data: Any,
                      status: str, error: Optional[str] = None) -> str:
        """Records an action into actions.json and updates stats."""
        action_count = len(self.actions) + 1
        action_id = f"ACT-{action_count:05d}"
        envelope = {
            "action_id": action_id,
            "mission_id": self.mission_id,
            "agent": agent.upper(),
            "timestamp": datetime.now().isoformat(),
            "input": input_data,
            "output": output_data,
            "status": status.upper(),
            "error": error
        }
        self.actions.append(envelope)
        
        # Update counters
        if agent.upper() == "HERMES":
            self.mission_data["stats"]["hermes_actions"] += 1
        elif agent.upper() == "CHATGPT":
            self.mission_data["stats"]["chatgpt_turns"] += 1
        elif agent.upper() == "GEMINI":
            self.mission_data["stats"]["gemini_turns"] += 1
            
        if status.upper() == "ERROR":
            self.mission_data["stats"]["total_errors"] += 1
            
        self.save_all()
        return action_id

    def record_chatgpt_message(self, role: str, content: str, parsed_protocol: Optional[Dict[str, Any]] = None):
        """Records a turn in ChatGPT conversation history."""
        entry = {
            "turn_id": len(self.conversation_chatgpt) + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "protocol_parsed": parsed_protocol
        }
        self.conversation_chatgpt.append(entry)
        self.save_all()

    def record_gemini_interaction(self, prompt: str, result: Dict[str, Any]):
        """Records an interaction in Gemini history."""
        entry = {
            "interaction_id": len(self.conversation_gemini) + 1,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        self.conversation_gemini.append(entry)
        self.save_all()

    def record_artifact(self, filename: str, file_path: str, file_type: str,
                        dimensions: str = "N/A", source_agent: str = "GEMINI") -> Dict[str, Any]:
        """Registers a newly created artifact (image, diagram, report, file)."""
        p = Path(file_path)
        size_bytes = p.stat().st_size if p.exists() else 0
        art_id = f"ART-{len(self.artifacts) + 1:04d}"
        art = {
            "artifact_id": art_id,
            "mission_id": self.mission_id,
            "filename": filename,
            "file_path": str(file_path),
            "file_type": file_type.upper(),
            "size_bytes": size_bytes,
            "dimensions": dimensions,
            "created_at": datetime.now().isoformat(),
            "source_agent": source_agent.upper()
        }
        self.artifacts.append(art)
        self.save_all()
        return art

    def update_mission_status(self, status: str, current_agent: Optional[str] = None,
                              target_agent: Optional[str] = None, iteration: Optional[int] = None):
        """Updates main mission status and metadata."""
        self.mission_data["status"] = status.upper()
        if current_agent:
            self.mission_data["current_agent"] = current_agent.upper()
        if target_agent:
            self.mission_data["next_target_agent"] = target_agent.upper()
        if iteration is not None:
            self.mission_data["current_iteration"] = iteration
        self.save_all()
