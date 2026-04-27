"""
Modul zur automatischen Erkennung verfügbarer Laufwerke.
"""
import os
import platform
import logging
import shutil
from typing import List, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None


class DiskDetector:
    """Erkennt automatisch alle verfügbaren Laufwerke im System."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.os_type = platform.system()
    
    def detect_all_drives(self, excluded_drives: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Erkennt alle verfügbaren Laufwerke im System.

        Args:
            excluded_drives: Liste von Pfaden oder Namen, die ausgeschlossen werden sollen.
        
        Returns:
            Liste von Dictionaries mit 'path' und 'name' Schlüsseln
        """
        if self.os_type == "Windows":
            drives = self._detect_windows_drives()
        elif self.os_type == "Darwin":
            drives = self._detect_macos_drives()
        elif self.os_type == "Linux":
            drives = self._detect_linux_drives()
        else:
            self.logger.warning(f"Unbekanntes Betriebssystem: {self.os_type}")
            drives = self._detect_psutil_drives()

        return self.filter_drives(drives, excluded_drives or [])

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalisiert Pfade für stabile Vergleiche."""
        expanded = os.path.abspath(os.path.expanduser(path))
        normalized = os.path.normcase(os.path.realpath(expanded))
        return normalized.rstrip("\\/")

    def filter_drives(
        self,
        drives: List[Dict[str, str]],
        excluded_drives: List[str],
    ) -> List[Dict[str, str]]:
        """
        Entfernt ausgeschlossene Laufwerke aus der erkannten Liste.

        Einträge in excluded_drives können entweder Pfade (z.B. "D:\\" oder
        "/Volumes/Backup") oder Laufwerksnamen sein.
        """
        if not excluded_drives:
            return drives

        excluded_paths = set()
        excluded_names = set()

        for item in excluded_drives:
            if not isinstance(item, str) or not item.strip():
                continue

            stripped = item.strip()
            excluded_names.add(stripped.casefold())

            try:
                excluded_paths.add(self._normalize_path(stripped))
            except OSError:
                pass

        filtered_drives = []
        for drive in drives:
            path = drive.get("path", "")
            name = drive.get("name", "")
            normalized_path = self._normalize_path(path) if path else ""

            if normalized_path in excluded_paths or name.casefold() in excluded_names:
                self.logger.info(f"Laufwerk ausgeschlossen: {name} ({path})")
                continue

            filtered_drives.append(drive)

        return filtered_drives

    def _detect_psutil_drives(self) -> List[Dict[str, str]]:
        """Erkennt Laufwerke plattformübergreifend über psutil."""
        if psutil is None:
            self.logger.debug("psutil ist nicht installiert, nutze Standardbibliothek-Fallback")
            return self._detect_fallback_drives()

        drives = []
        seen_mounts = set()
        seen_usage = set()

        for partition in psutil.disk_partitions(all=False):
            mount_point = partition.mountpoint
            if not mount_point:
                continue

            if self._should_skip_mount(mount_point):
                continue

            try:
                usage = psutil.disk_usage(mount_point)
            except (OSError, PermissionError):
                self.logger.debug(f"Nicht zugängliches Laufwerk übersprungen: {mount_point}")
                continue

            normalized = self._normalize_path(mount_point)
            if normalized in seen_mounts:
                continue

            usage_signature = (usage.total, usage.free)
            if self.os_type == "Darwin" and usage_signature in seen_usage:
                self.logger.debug(f"Doppeltes macOS-Volume übersprungen: {mount_point}")
                continue

            seen_mounts.add(normalized)
            seen_usage.add(usage_signature)
            drives.append({
                "path": mount_point,
                "name": self._format_drive_name(mount_point, partition.device),
            })

        return drives

    def _should_skip_mount(self, mount_point: str) -> bool:
        """Filtert technische Mounts, die nicht sinnvoll überwacht werden."""
        if self.os_type == "Darwin":
            name = os.path.basename(mount_point.rstrip("/\\"))
            return name.startswith("com.apple.") or mount_point.startswith("/System/Volumes/")

        return False

    def _detect_fallback_drives(self) -> List[Dict[str, str]]:
        """Fallback-Erkennung ohne optionale Abhängigkeiten."""
        if self.os_type == "Windows":
            return self._detect_windows_drives_without_psutil()

        if self.os_type == "Darwin":
            drives = [{"path": "/", "name": "Hauptfestplatte"}]
            root_usage = shutil.disk_usage("/")
            seen_usage = {(root_usage.total, root_usage.free)}
            volumes_path = "/Volumes"
            if os.path.exists(volumes_path):
                seen_paths = {self._normalize_path("/")}
                try:
                    for volume in os.listdir(volumes_path):
                        if volume.startswith("com.apple."):
                            continue

                        volume_path = os.path.join(volumes_path, volume)
                        if not os.path.isdir(volume_path):
                            continue

                        try:
                            usage = shutil.disk_usage(volume_path)
                        except OSError:
                            continue

                        normalized_path = self._normalize_path(volume_path)
                        if normalized_path in seen_paths:
                            continue

                        usage_signature = (usage.total, usage.free)
                        if usage_signature in seen_usage:
                            continue

                        seen_paths.add(normalized_path)
                        seen_usage.add(usage_signature)
                        drives.append({"path": volume_path, "name": volume})
                except OSError as e:
                    self.logger.debug(f"Fehler beim Auflisten von /Volumes: {e}")

            return drives

        if self.os_type == "Linux":
            drives = []
            for mount_path in ["/", "/home", "/var", "/mnt", "/media"]:
                if not os.path.exists(mount_path):
                    continue

                try:
                    shutil.disk_usage(mount_path)
                except OSError:
                    continue

                drives.append({"path": mount_path, "name": self._format_drive_name(mount_path)})

            return drives

        return []

    def _detect_windows_drives_without_psutil(self) -> List[Dict[str, str]]:
        """Fallback-Erkennung für Windows-Laufwerksbuchstaben."""
        import string

        drives = []
        for letter in string.ascii_uppercase:
            path = f"{letter}:\\"
            try:
                shutil.disk_usage(path)
            except OSError:
                continue

            drives.append({"path": path, "name": f"Laufwerk {letter}"})

        return drives

    def _format_drive_name(self, mount_point: str, device: str = "") -> str:
        """Erzeugt einen lesbaren Namen für ein Laufwerk."""
        if self.os_type == "Windows":
            return f"Laufwerk {mount_point[:1].upper()}"

        if mount_point == "/":
            return "Hauptfestplatte"

        name = os.path.basename(mount_point.rstrip("/\\")) or device or mount_point
        return name
    
    def _detect_windows_drives(self) -> List[Dict[str, str]]:
        """Erkennt Windows-Laufwerke (C:, D:, E:, etc.)"""
        drives = self._detect_psutil_drives()
        for drive in drives:
            self.logger.info(f"Gefundenes Windows-Laufwerk: {drive['path']}")

        return drives
    
    def _detect_macos_drives(self) -> List[Dict[str, str]]:
        """Erkennt macOS-Laufwerke"""
        drives = self._detect_psutil_drives()
        if not any(drive["path"] == "/" for drive in drives):
            drives.insert(0, {"path": "/", "name": "Hauptfestplatte"})

        for drive in drives:
            self.logger.info(f"Gefundenes macOS-Laufwerk: {drive['path']}")

        return drives
    
    def _detect_linux_drives(self) -> List[Dict[str, str]]:
        """Erkennt Linux-Partitionen"""
        drives = self._detect_psutil_drives()
        for drive in drives:
            self.logger.info(f"Gefundene Linux-Partition: {drive['path']}")

        return drives


def main():
    """Hilfsfunktion zum Testen der Laufwerk-Erkennung."""
    logging.basicConfig(level=logging.INFO)
    detector = DiskDetector()
    drives = detector.detect_all_drives()
    
    print(f"\nGefundene Laufwerke ({len(drives)}):")
    print("-" * 50)
    for drive in drives:
        print(f"  Path: {drive['path']:<20} Name: {drive['name']}")


if __name__ == "__main__":
    main()
