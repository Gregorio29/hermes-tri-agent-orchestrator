"""
Mission Manager for Lifecycle and Mission Registry
Location: I:\\Proyectos\\Hermes\\Proyectos\\ChatGPTBridge\\core\\mission_manager.py
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import MISSIONS_DIR, STATE_DIR
from core.state_manager import StateManager

class MissionManager:
    def __init__(self, missions_dir: Optional[Path] = None):
        self.missions_dir = Path(missions_dir) if missions_dir else MISSIONS_DIR
        self.missions_dir.mkdir(parents=True, exist_ok=True)

    def create_mission(self, title: str, description: str) -> StateManager:
        """Creates and initializes a new mission."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        clean_title = "".join(c for c in title if c.isalnum() or c in ("-", "_")).lower()[:20]
        mission_id = f"MIS-{timestamp}-{clean_title}"
        
        state_mgr = StateManager(mission_id=mission_id)
        state_mgr.mission_data["title"] = title
        state_mgr.mission_data["description"] = description
        state_mgr.mission_data["status"] = "INITIALIZED"
        state_mgr.save_all()
        return state_mgr

    def load_mission(self, mission_id: str) -> Optional[StateManager]:
        """Loads an existing mission state."""
        mission_path = self.missions_dir / mission_id / "mission.json"
        if not mission_path.exists():
            return None
        return StateManager(mission_id=mission_id)

    def list_missions(self) -> List[Dict[str, Any]]:
        """Lists all missions present in missions directory."""
        missions = []
        for m_dir in self.missions_dir.iterdir():
            if m_dir.is_dir():
                m_file = m_dir / "mission.json"
                if m_file.exists():
                    try:
                        with open(m_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            missions.append(data)
                    except Exception:
                        pass
        # Sort newest first
        missions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return missions

    def get_latest_mission(self) -> Optional[StateManager]:
        """Returns the most recent mission."""
        missions = self.list_missions()
        if missions:
            return self.load_mission(missions[0]["mission_id"])
        return None
