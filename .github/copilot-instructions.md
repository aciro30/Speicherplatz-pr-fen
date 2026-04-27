# Speicherplatz-Überwachung - Projekt-Dokumentation

Dieses Projekt implementiert eine automatische Festplatten-Überwachungslösung mit E-Mail-Benachrichtigungen.

## Projektübersicht

- **Sprache**: Python 3.7+
- **Hauptzweck**: Kontinuierliche Überwachung von Festplattenspeicher mit konfigurierbaren Schwellwerten
- **Ausgabemechanismus**: E-Mail-Benachrichtigungen bei kritischem Speicherplatz

## Projektstruktur

- `src/disk_monitor.py` - Hauptmodul mit CLI und Daemon-Modus
- `src/disk_checker.py` - Speicherplatzbelegung auslesen
- `src/config_manager.py` - JSON-Konfigurationsverwaltung
- `src/email_notifier.py` - SMTP-basierte E-Mail-Versendung
- `config/config.example.json` - Konfigurationsvorlage
- `logs/` - Verzeichnis für Log-Dateien

## Kernfunktionalität

1. **Disk Checking**: Liest Speicherauslastung aller konfigurierten Laufwerke aus
2. **Threshold Comparison**: Vergleicht Auslastung mit konfiguriertem Schwellwert
3. **Email Alert**: Versendet SMTP-E-Mails bei Überschreitung
4. **Daemon Mode**: Kontinuierliche Überwachung im Hintergrund
5. **Logging**: Detaillierte Protokollierung aller Aktionen

## Verwendete Bibliotheken

- `psutil` - Systemressourcen-Informationen
- `smtplib` - E-Mail-Versand über SMTP
- Python Standard Library: `shutil`, `json`, `logging`, `argparse`

## Konfiguration

Die Anwendung wird über `config/config.json` konfiguriert mit folgenden Schlüsseln:
- `storage_threshold_percent` - Schwellwert (0-100)
- `drives_to_monitor` - Liste der zu überwachenden Pfade
- `email` - SMTP-Konfiguration und Empfänger
- `check_interval_seconds` - Prüfintervall im Daemon-Modus
- `logging` - Log-Level und Dateipfad

## Nutzung

```bash
# Einmalige Prüfung
python src/disk_monitor.py

# Daemon-Modus
python src/disk_monitor.py --daemon

# Mit benutzerdefinierter Konfiguration
python src/disk_monitor.py --config /pfad/zur/config.json
```

## Nächste Schritte (optional)

- Docker-Support für containerisierte Ausführung
- Systemd Service für Linux-Automatisierung
- Windows Service Wrapper für Windows
- Datenbankprotokollierung für Verlaufsanalyse
- Web-Dashboard für Monitoring
- SMS/Slack/Teams-Benachrichtigungen
