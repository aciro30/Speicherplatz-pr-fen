"""
Modul zur Prüfung des Speicherplatzes.
"""
import shutil
import platform
import subprocess
from typing import Dict, List


class DiskChecker:
    """Prüft den Speicherplatz von Festplatten."""
    
    @staticmethod
    def get_disk_usage(path: str) -> Dict[str, float]:
        """
        Ermittelt die Speicherplatzbelegung für ein Laufwerk.
        
        Args:
            path: Pfad zum Laufwerk oder Ordner (z.B. 'C:\\', 'D:\\', '/', '/home')
            
        Returns:
            Dictionary mit Informationen zu Speicher, verwendet, frei und Prozent
            
        Raises:
            FileNotFoundError: Falls der Pfad nicht existiert
            OSError: Bei Zugriffsproblemen
        """
        try:
            # Normalisiere Pfad für das Betriebssystem
            normalized_path = str(path).strip()
            usage = shutil.disk_usage(normalized_path)
            total = usage.total
            used = usage.used
            free = usage.free
            
            # Konvertiere zu Gigabyte
            total_gb = total / (1024 ** 3)
            used_gb = used / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            
            # Berechne Prozentsatz
            percent_used = (used / total * 100) if total > 0 else 0
            
            return {
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent_used": round(percent_used, 2)
            }
        except FileNotFoundError:
            raise FileNotFoundError(f"Pfad nicht gefunden: {path}")
        except OSError as e:
            raise OSError(f"Fehler beim Zugriff auf {path}: {e}")
    
    @staticmethod
    def get_all_drives() -> List[Dict[str, str]]:
        """
        Ermittelt automatisch alle verfügbaren Laufwerke des Systems.
        
        Returns:
            Liste mit Laufwerk-Informationen (path, name)
        """
        drives = []
        system = platform.system()
        
        if system == "Windows":
            # Windows: Alle Laufwerksbuchstaben durchsuchen
            import string
            for drive in string.ascii_uppercase:
                drive_path = f"{drive}:\\"
                try:
                    shutil.disk_usage(drive_path)
                    drives.append({
                        "path": drive_path,
                        "name": f"Laufwerk {drive}"
                    })
                except OSError:
                    # Laufwerk existiert nicht
                    pass
                    
        elif system == "Darwin":
            # macOS: /Volumes durchsuchen
            try:
                import os
                volumes_path = "/Volumes"
                if os.path.exists(volumes_path):
                    # Hauptfestplatte
                    drives.append({
                        "path": "/",
                        "name": "Hauptfestplatte"
                    })
                    # Externe Laufwerke
                    for item in os.listdir(volumes_path):
                        item_path = os.path.join(volumes_path, item)
                        if os.path.isdir(item_path):
                            try:
                                shutil.disk_usage(item_path)
                                drives.append({
                                    "path": item_path,
                                    "name": f"Laufwerk: {item}"
                                })
                            except OSError:
                                pass
            except Exception:
                # Fallback
                drives.append({
                    "path": "/",
                    "name": "Hauptfestplatte"
                })
                
        elif system == "Linux":
            # Linux: Typische Mountpunkte
            common_mounts = ["/", "/home", "/mnt", "/media"]
            for mount_path in common_mounts:
                try:
                    shutil.disk_usage(mount_path)
                    drives.append({
                        "path": mount_path,
                        "name": f"Partition: {mount_path}"
                    })
                except OSError:
                    pass
        
        return drives
