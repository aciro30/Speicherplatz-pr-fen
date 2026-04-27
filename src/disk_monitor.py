"""
Hauptmodul für die Speicherplatz-Überwachung.
"""
import logging
import time
import os

from config_manager import ConfigManager
from disk_checker import DiskChecker
from disk_detector import DiskDetector
from email_notifier import EmailNotifier


class DiskMonitor:
    """Überwacht Festplattenspeicher und sendet E-Mail-Benachrichtigungen."""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialisiert den Disk Monitor.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        if not self.config_manager.validate_config(self.config):
            raise ValueError("Ungültige Konfiguration")

        self._setup_logging()
        self.disk_checker = DiskChecker()
        self.disk_detector = DiskDetector()
        self.email_notifier = EmailNotifier(self.config.get("email", {}))
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """Konfiguriert das Logging-System."""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        log_file = log_config.get("log_file", "logs/disk_monitor.log")
        
        # Erstelle Log-Verzeichnis falls nicht vorhanden
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def _get_drives_to_monitor(self) -> list:
        """Ermittelt die zu überwachenden Laufwerke aus Konfiguration oder Auto-Detection."""
        auto_detect = self.config.get("auto_detect_drives", False)

        if auto_detect:
            excluded_drives = self.config.get("excluded_drives", [])
            drives = self.disk_detector.detect_all_drives(excluded_drives)
            self.logger.info(f"Auto-Detection aktiv: {len(drives)} Laufwerk(e) gefunden")
            return drives

        return self.config.get("drives_to_monitor", [])

    def check_drives(self) -> list:
        """
        Prüft alle konfigurierten Festplatten auf Speicherplatz.
        
        Returns:
            Liste mit kritischen Laufwerken
        """
        threshold = self.config.get("storage_threshold_percent", 80)
        drives = self._get_drives_to_monitor()
        critical_drives = []
        
        if not drives:
            self.logger.warning("Keine Laufwerke in der Konfiguration definiert!")
            return critical_drives
        
        self.logger.info(f"Starte Speicherplatz-Prüfung (Schwelle: {threshold}%)")
        
        for drive in drives:
            path = drive.get("path")
            name = drive.get("name", path)
            
            try:
                usage = self.disk_checker.get_disk_usage(path)
                percent_used = usage["percent_used"]
                
                self.logger.info(
                    f"{name} ({path}): {percent_used}% belegt "
                    f"({usage['used_gb']:.2f}GB / {usage['total_gb']:.2f}GB)"
                )
                
                if percent_used >= threshold:
                    self.logger.warning(
                        f"KRITISCH: {name} hat {percent_used}% Speicher belegt!"
                    )
                    critical_drives.append({
                        "name": name,
                        "path": path,
                        "percent_used": percent_used,
                        "used_gb": usage["used_gb"],
                        "total_gb": usage["total_gb"],
                        "free_gb": usage["free_gb"]
                    })
            except Exception as e:
                self.logger.error(f"Fehler beim Prüfen von {name}: {e}")
                
        return critical_drives
    
    def handle_critical_drives(self, critical_drives: list):
        """
        Behandelt kritische Laufwerke durch E-Mail-Benachrichtigung.
        
        Args:
            critical_drives: Liste mit kritischen Laufwerken
        """
        if not critical_drives:
            return
            
        email_config = self.config.get("email", {})
        if not email_config.get("enabled", False):
            self.logger.info("E-Mail-Benachrichtigungen sind deaktiviert")
            return
        
        try:
            self.email_notifier.send_alert(critical_drives)
            self.logger.info(f"E-Mail-Benachrichtigung für {len(critical_drives)} Laufwerk(e) gesendet")
        except Exception as e:
            self.logger.error(f"Fehler beim E-Mail-Versand: {e}")
    
    def run_once(self):
        """Führt eine Speicherplatz-Prüfung durch."""
        self.logger.info("=" * 60)
        critical_drives = self.check_drives()
        self.handle_critical_drives(critical_drives)
        self.logger.info("=" * 60)
    
    def run_daemon(self):
        """Führt die Überwachung im Daemon-Modus aus."""
        interval = self.config.get("check_interval_seconds", 3600)
        self.logger.info(f"Starte Daemon-Modus (Prüfintervall: {interval} Sekunden)")
        
        try:
            while True:
                self.run_once()
                self.logger.info(f"Nächste Prüfung in {interval} Sekunden...")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("Daemon-Modus beendet")


def main():
    """Haupteinstiegspunkt."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speicherplatz-Überwachung mit E-Mail-Benachrichtigungen"
    )
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Pfad zur Konfigurationsdatei (Standard: config/config.json)"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Führt das Programm im Daemon-Modus aus (kontinuierliche Überwachung)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Führt nur eine Prüfung durch und beendet sich (Standard)"
    )
    
    args = parser.parse_args()
    
    monitor = DiskMonitor(args.config)
    
    if args.daemon:
        monitor.run_daemon()
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()
