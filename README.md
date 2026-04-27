# Speicherplatz-Überwachung

Ein Python-Programm zur automatischen Überwachung des Speicherplatzes auf Festplatten mit E-Mail-Benachrichtigungen bei kritischem Speicherplatz.

## Features

- ✅ Überwachung mehrerer Festplatten/Laufwerke
- ✅ Automatische Laufwerkserkennung mit Ausschlussliste
- ✅ Konfigurierbare Speicherplatz-Schwellen (in Prozent)
- ✅ Automatische E-Mail-Benachrichtigungen
- ✅ Daemon-Modus für kontinuierliche Überwachung
- ✅ Detailliertes Logging
- ✅ Einfache JSON-Konfiguration

## Installation

### Voraussetzungen
- Python 3.7 oder höher
- pip (Python Package Manager)

### Schritt 1: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Unter Windows kann stattdessen das Setup-Skript verwendet werden:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Mit Aufgabenplanung alle 12 Stunden:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask
```

### Schritt 2: Konfiguration erstellen

1. Kopiere die Beispielkonfiguration:
```bash
cp config/config.example.json config/config.json
```

2. Bearbeite `config/config.json` mit deinen Einstellungen:
   - **storage_threshold_percent**: Schwellenwert in Prozent (z.B. 80 = Warnung bei 80% Auslastung)
   - **auto_detect_drives**: `true` erkennt alle Laufwerke automatisch
   - **excluded_drives**: Liste der Laufwerke, die bei Auto-Detection ignoriert werden sollen
   - **drives_to_monitor**: Manuelle Liste der Laufwerke, wenn `auto_detect_drives` auf `false` steht
   - **email**: E-Mail-Einstellungen (SMTP-Server, Absender, Empfänger)

Alternativ kann die Konfiguration automatisch erzeugt werden:

```bash
python src/setup_config.py
```

Das erzeugt eine statische Liste der aktuell vorhandenen Laufwerke. Wenn Laufwerke bei jedem Monitorlauf neu erkannt werden sollen:

```bash
python src/setup_config.py --auto-detect
```

Eine bestehende Konfiguration wird nur mit `--overwrite` ersetzt:

```bash
python src/setup_config.py --overwrite
```

### Beispiel-Konfiguration für macOS:

```json
{
  "check_interval_seconds": 3600,
  "storage_threshold_percent": 80,
  "auto_detect_drives": true,
  "excluded_drives": [
    "/Volumes/Backup"
  ],
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "deine-email@gmail.com",
    "sender_password": "dein-app-passwort",
    "recipient_emails": ["admin@example.com"],
    "email_subject": "Warnung: Speicherplatz kritisch"
  },
  "drives_to_monitor": [],
  "logging": {
    "level": "INFO",
    "log_file": "logs/disk_monitor.log"
  }
}
```

### Beispiel-Konfiguration für Windows:

```json
{
  "check_interval_seconds": 3600,
  "storage_threshold_percent": 80,
  "auto_detect_drives": true,
  "excluded_drives": [
    "D:\\"
  ],
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "deine-email@gmail.com",
    "sender_password": "dein-app-passwort",
    "recipient_emails": ["admin@example.com"],
    "email_subject": "Warnung: Speicherplatz kritisch"
  },
  "drives_to_monitor": [],
  "logging": {
    "level": "INFO",
    "log_file": "logs/disk_monitor.log"
  }
}
```

**Wichtig für Windows-Pfade**: 
- Verwende Backslashes: `C:\` oder in JSON mit Escaping: `C:\\`
- Oder verwende Slashes: `C:/` (funktioniert auch)
- Alle verfügbaren Laufwerke können überwacht werden (C:, D:, E:, usw.)

### Beispiel-Konfiguration für manuelle Laufwerksliste:

```json
{
  "auto_detect_drives": false,
  "excluded_drives": [],
  "drives_to_monitor": [
    {
      "path": "/",
      "name": "Root-Partition"
    },
    {
      "path": "/home",
      "name": "Home-Partition"
    }
  ],
  ...
}
```

Bei aktivierter Auto-Detection können in `excluded_drives` Pfade oder Namen stehen, z.B. `D:\\`, `/Volumes/Backup` oder `Backup`.

## Verwendung

### Einmalige Prüfung

```bash
python src/disk_monitor.py
```

Oder unter Windows (PowerShell oder CMD):
```cmd
py src\disk_monitor.py
```

### Daemon-Modus (kontinuierliche Überwachung)

```bash
python src/disk_monitor.py --daemon
```

Oder unter Windows (PowerShell oder CMD):
```cmd
py src\disk_monitor.py --daemon
```

### Mit benutzerdefinierten Konfigurationen

```bash
python src/disk_monitor.py --config /pfad/zur/config.json
python src/disk_monitor.py --config /pfad/zur/config.json --daemon
```

Oder unter Windows:
```cmd
py src\disk_monitor.py --config config\config.json
py src\disk_monitor.py --config config\config.json --daemon
```

## E-Mail-Konfiguration

### Gmail

1. Aktiviere 2-Faktor-Authentifizierung in deinem Google-Konto
2. Generiere ein [App-Passwort](https://myaccount.google.com/apppasswords)
3. Verwende dieses Passwort in der Konfiguration

### Andere E-Mail-Anbieter

Passe `smtp_server` und `smtp_port` an:
- **Outlook**: smtp.office365.com (587)
- **Yahoo**: smtp.mail.yahoo.com (587)
- **T-Online**: smtp.t-online.de (587)

### Mehrere Empfänger

Mehrere Empfänger werden in `recipient_emails` als JSON-Liste eingetragen:

```json
"recipient_emails": [
  "admin@example.com",
  "technik@example.com",
  "it-alerts@example.com"
]
```

Nicht als einzelner komma-getrennter String eintragen. Der E-Mail-Versand verbindet die Listeneinträge intern korrekt.

### Rechnername und lokale IP

Die Warn-E-Mail enthält automatisch den Rechnernamen und die lokale IP-Adresse. Dadurch ist auch bei mehreren Installationen erkennbar, von welchem Rechner die Meldung kommt.

## Automatische Ausführung

### Windows (Task Scheduler) - Empfohlen ⭐

Automatisch per Setup-Skript:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask
```

Das Skript erstellt `venv`, installiert die Abhängigkeiten, erzeugt `config\config.json`, führt einen Testlauf aus und registriert danach den Scheduled Task. Standardmäßig läuft die Aufgabe alle 12 Stunden.

Ein anderes Intervall kann in Minuten angegeben werden:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask -IntervalMinutes 60
```

**Einmalige Prüfung stündlich:**

1. Öffne **Task Scheduler** (Aufgabenplaner)
2. Wähle **Aufgabe erstellen** im rechten Menü
3. **Allgemein**:
   - Name: "Speicherplatz-Monitor"
   - Häkchen bei "Mit höchsten Privilegien ausführen"

4. **Trigger** (Zeitplan):
   - Klicke "Neu..."
   - Wähle "Täglich" oder "Stündlich"
   - Stelle das Zeitintervall ein

5. **Aktion**:
   - Programm/Skript: `py`
   - Argumente: `src\disk_monitor.py`
   - Arbeitsverzeichnis: `C:\pfad\zum\Speicherplatz-prüfen`

6. **Bedingungen**: Häkchen bei "Aufgabe auch ausführen, wenn der Benutzer nicht angemeldet ist"
7. Klicke **OK** zum Speichern

**Für Daemon-Modus bei Systemstart:**

Folge denselben Schritten, aber:
- **Trigger**: "Bei Systemstart"
- **Aktion - Argumente**: `src\disk_monitor.py --daemon`
- **Bedingungen - Allgemein**: 
  - Häkchen bei "Programm auch bei Fehler erneut starten"
  - Neustartintervall: "5 Minuten"

**Wichtig**: 
- Achte auf die richtige Arbeitsverzeichnis-Pfad
- Verwende Backslashes `\` im Task Scheduler
- Wenn `python` in PowerShell nicht funktioniert, verwende `py`. Das Setup-Skript selbst nutzt fuer die Aufgabe die Python-Datei aus `venv\Scripts\python.exe`.

### macOS/Linux (Cron)

Zum Ausführen alle 60 Minuten:

```bash
0 * * * * cd /pfad/zum/projekt && python src/disk_monitor.py
```

Oder für Daemon-Modus (bei Systemstart):
```bash
@reboot cd /pfad/zum/projekt && python src/disk_monitor.py --daemon &
```

### Docker

Ein Dockerfile kann später hinzugefügt werden für containerisierte Ausführung.

## Dateistruktur

```
Speicherplatz-prüfen/
├── src/
│   ├── disk_monitor.py       # Hauptmodul
│   ├── disk_checker.py       # Speicherplatz-Prüfung
│   ├── disk_detector.py      # Automatische Laufwerkserkennung
│   ├── setup_config.py       # Erstellt config.json aus erkannten Laufwerken
│   ├── config_manager.py     # Konfigurationsverwaltung
│   └── email_notifier.py     # E-Mail-Versand
├── config/
│   ├── config.example.json   # Beispielkonfiguration
│   └── config.json           # Aktuelle Konfiguration (nicht versioniert)
├── logs/
│   └── disk_monitor.log      # Log-Datei
├── setup.ps1                 # Windows-Setup inkl. optionalem Scheduled Task
├── requirements.txt          # Python-Abhängigkeiten
└── README.md                 # Diese Datei
```

## Logs

Die Log-Datei wird in `logs/disk_monitor.log` gespeichert. Dort können alle Prüfungen und Fehler nachverfolgt werden.

## Troubleshooting

### "Konfigurationsdatei nicht gefunden"
- Stelle sicher, dass `config/config.json` existiert
- Kopiere `config/config.example.json` zu `config/config.json`

### "Python-Befehl nicht gefunden" (Windows)
- Stelle sicher, dass Python installiert ist und im PATH liegt
- Test: Öffne CMD und gib `python --version` ein
- Falls nicht gefunden: Nutze den vollständigen Pfad zu Python, z.B. `C:\Python\python.exe src\disk_monitor.py`

### "E-Mail konnte nicht versendet werden"
- Prüfe Absender-Adresse und Passwort in der Konfiguration
- Prüfe SMTP-Server und Port-Einstellungen
- Prüfe Firewall/Proxy-Einstellungen
- Für Gmail: Stelle sicher, dass ein [App-Passwort](https://myaccount.google.com/apppasswords) verwendet wird
- Test der E-Mail-Einstellung: Bearbeite die Konfiguration und aktiviere `"enabled": true`

### "Zugriff verweigert auf Laufwerk" (Windows)
- Führe das Programm mit Administratorrechten aus
- Im Task Scheduler: Häkchen bei "Mit höchsten Privilegien ausführen"

### Pfade funktionieren nicht
- Windows: Verwende `C:\` (mit Backslash) oder `C:/` (mit Slash)
- macOS: `/` für Hauptfestplatte, `/Volumes/...` für externe Festplatten
- Linux: `/` für Root, `/home`, `/mnt`, etc.
- Tipp: Nutze absolute Pfade, nicht relative Pfade

### Log-Datei ansehen
Die Log-Datei befindet sich unter `logs/disk_monitor.log`
- Windows: Öffne die Datei mit einem Texteditor
- macOS/Linux: `cat logs/disk_monitor.log` oder `tail -f logs/disk_monitor.log`

## Lizenz

MIT

## Support

Bei Fragen oder Problemen, überprüfe die Logs und stelle sicher, dass die Konfiguration korrekt ist.
