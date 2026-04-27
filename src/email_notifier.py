"""
Modul zur Versendung von E-Mail-Benachrichtigungen.
"""
import logging
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any


class EmailNotifier:
    """Versendet E-Mail-Benachrichtigungen bei kritischem Speicherplatz."""
    
    def __init__(self, email_config: Dict[str, Any]):
        """
        Initialisiert den EmailNotifier.
        
        Args:
            email_config: Dictionary mit E-Mail-Konfigurationseinstellungen
        """
        self.config = email_config
        self.logger = logging.getLogger(__name__)
        
    def send_alert(self, critical_drives: List[Dict[str, Any]]):
        """
        Versendet eine Benachrichtigungs-E-Mail.
        
        Args:
            critical_drives: Liste mit kritischen Laufwerken
            
        Raises:
            ValueError: Falls E-Mail-Konfiguration unvollständig ist
            smtplib.SMTPException: Falls E-Mail-Versand fehlschlägt
        """
        if not self._validate_config():
            raise ValueError("Unvollständige E-Mail-Konfiguration")
        
        sender = self.config.get("sender_email")
        recipients = self.config.get("recipient_emails", [])
        
        if not recipients:
            raise ValueError("Keine Empfänger definiert")
        
        subject = self.config.get("email_subject", "Warnung: Speicherplatz kritisch")
        body = self._generate_email_body(critical_drives)
        
        self._send_email(sender, recipients, subject, body)
    
    def _validate_config(self) -> bool:
        """
        Validiert die E-Mail-Konfiguration.
        
        Returns:
            True falls gültig, False sonst
        """
        required_fields = ["smtp_server", "smtp_port", "sender_email", 
                          "sender_password", "recipient_emails"]
        
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"E-Mail-Konfigurationsfeld fehlt: {field}")
                return False
        
        return True
    
    def _generate_email_body(self, critical_drives: List[Dict[str, Any]]) -> str:
        """
        Generiert den E-Mail-Body.
        
        Args:
            critical_drives: Liste mit kritischen Laufwerken
            
        Returns:
            Formatierter E-Mail-Text
        """
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        system_info = self._get_system_info()
        
        body = f"""
Speicherplatz-Warnung
=====================

Zeitstempel: {timestamp}
Rechnername: {system_info['hostname']}
Lokale IP-Adresse: {system_info['local_ip']}

Die folgenden Laufwerke haben den kritischen Speicherplatz-Schwellenwert überschritten:

"""
        
        for drive in critical_drives:
            body += f"""
Laufwerk: {drive['name']}
Pfad: {drive['path']}
Belegt: {drive['percent_used']}%
Verwendet: {drive['used_gb']:.2f} GB
Verfügbar: {drive['free_gb']:.2f} GB
Gesamtkapazität: {drive['total_gb']:.2f} GB

---
"""
        
        body += """
Bitte überprüfen Sie die Speicherauslastung und ergreifen Sie entsprechende Maßnahmen.

Mit freundlichen Grüßen,
Ihr Speicherplatz-Monitor
"""
        
        return body

    def _get_system_info(self) -> Dict[str, str]:
        """Ermittelt Rechnername und lokale IP-Adresse fuer die Benachrichtigung."""
        hostname = socket.gethostname()
        local_ip = "Unbekannt"

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                local_ip = sock.getsockname()[0]
        except OSError:
            try:
                local_ip = socket.gethostbyname(hostname)
            except OSError:
                self.logger.debug("Lokale IP-Adresse konnte nicht ermittelt werden")

        return {
            "hostname": hostname,
            "local_ip": local_ip,
        }
    
    def _send_email(self, sender: str, recipients: List[str], 
                   subject: str, body: str):
        """
        Versendet die E-Mail über SMTP.
        
        Args:
            sender: Absender-E-Mail-Adresse
            recipients: Liste der Empfänger-E-Mail-Adressen
            subject: E-Mail-Betreffzeile
            body: E-Mail-Body
            
        Raises:
            smtplib.SMTPException: Falls E-Mail-Versand fehlschlägt
        """
        smtp_server = self.config.get("smtp_server")
        smtp_port = self.config.get("smtp_port")
        password = self.config.get("sender_password")
        
        try:
            self.logger.info(f"Verbinde zu SMTP-Server: {smtp_server}:{smtp_port}")
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                
                # Erstelle E-Mail-Nachricht
                message = MIMEMultipart()
                message["From"] = sender
                message["To"] = ", ".join(recipients)
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain", "utf-8"))
                
                # Versende E-Mail
                server.send_message(message)
                
            self.logger.info(f"E-Mail an {len(recipients)} Empfänger versendet")
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("SMTP-Authentifizierungsfehler (falsches Passwort?)")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP-Fehler: {e}")
            raise
