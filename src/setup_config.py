"""
Erstellt eine Konfiguration mit automatisch erkannten Laufwerken.
"""
import argparse
import logging
from pathlib import Path

from config_manager import ConfigManager
from disk_detector import DiskDetector


def build_config(config_path: str, threshold: int, overwrite: bool, auto_detect: bool) -> bool:
    """
    Erstellt eine config.json mit allen aktuell verfügbaren Laufwerken.

    Returns:
        True, wenn eine Konfiguration gespeichert wurde, sonst False.
    """
    path = Path(config_path)
    if path.exists() and not overwrite:
        print(f"Konfiguration existiert bereits: {path}")
        print("Nutze --overwrite, um sie neu zu erzeugen.")
        return False

    detector = DiskDetector()
    drives = detector.detect_all_drives()

    config = {
        "check_interval_seconds": 3600,
        "storage_threshold_percent": threshold,
        "auto_detect_drives": auto_detect,
        "excluded_drives": [],
        "email": {
            "enabled": False,
            "recipient_emails": ["admin@example.com"],
            "email_subject": "Warnung: Speicherplatz kritisch",
        },
        "drives_to_monitor": drives,
        "logging": {
            "level": "INFO",
            "log_file": "logs/disk_monitor.log",
        },
    }

    ConfigManager(str(path)).save_config(config)

    print(f"Konfiguration erstellt: {path}")
    print(f"Gefundene Laufwerke: {len(drives)}")
    for drive in drives:
        print(f"- {drive['name']}: {drive['path']}")

    return True


def main():
    """CLI-Einstiegspunkt."""
    parser = argparse.ArgumentParser(
        description="Erstellt config/config.json mit automatisch erkannten Laufwerken"
    )
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Zielpfad der Konfiguration (Standard: config/config.json)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Speicherplatz-Schwelle in Prozent (Standard: 80)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Bestehende Konfiguration überschreiben",
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Dynamische Laufwerkserkennung bei jedem Monitorlauf aktivieren",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    build_config(args.config, args.threshold, args.overwrite, args.auto_detect)


if __name__ == "__main__":
    main()
