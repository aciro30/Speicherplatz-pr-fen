"""
Modul zur Verwaltung der Konfiguration.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Verwaltet die Konfigurationsdatei."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialisiert den ConfigManager.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """
        Lädt die Konfiguration aus der JSON-Datei.
        
        Returns:
            Dictionary mit den Konfigurationseinstellungen
            
        Raises:
            FileNotFoundError: Falls die Konfigurationsdatei nicht existiert
            json.JSONDecodeError: Falls die JSON-Datei ungültig ist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Konfigurationsdatei nicht gefunden: {self.config_path}\n"
                f"Bitte kopiere config/config.example.json zu config/config.json"
            )
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.logger.info(f"Konfiguration geladen: {self.config_path}")
            return config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Fehler beim Parsen der Konfigurationsdatei: {e}",
                e.doc,
                e.pos
            )
    
    def save_config(self, config: Dict[str, Any]):
        """
        Speichert die Konfiguration in der JSON-Datei.
        
        Args:
            config: Dictionary mit den Konfigurationseinstellungen
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Konfiguration gespeichert: {self.config_path}")
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validiert die Konfiguration.
        
        Args:
            config: Dictionary mit den Konfigurationseinstellungen
            
        Returns:
            True falls gültig, False sonst
        """
        required_fields = ["storage_threshold_percent"]
        
        for field in required_fields:
            if field not in config:
                logging.warning(f"Erforderliches Konfigurationsfeld fehlt: {field}")
                return False
        
        threshold = config.get("storage_threshold_percent", 0)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
            logging.warning("storage_threshold_percent muss zwischen 0 und 100 liegen")
            return False
        
        auto_detect = config.get("auto_detect_drives", False)
        if not isinstance(auto_detect, bool):
            logging.warning("auto_detect_drives muss true oder false sein")
            return False

        drives = config.get("drives_to_monitor", [])
        if not auto_detect and (not isinstance(drives, list) or len(drives) == 0):
            logging.warning("drives_to_monitor muss eine nicht-leere Liste sein, wenn auto_detect_drives false ist")
            return False

        excluded_drives = config.get("excluded_drives", [])
        if not isinstance(excluded_drives, list):
            logging.warning("excluded_drives muss eine Liste sein")
            return False
        
        return True
