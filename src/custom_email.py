#!/usr/bin/env python3

import os
import logging
import smtplib
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from typing import List, Union, Optional
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("ZohoEmailer")


class ZohoEmailer:
    """Enhanced Zoho email sender with proper HTML support"""

    MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        # NOTE: Change extension if your account is outside the US (.eu, .in, .com.au)
        self.smtp_server = "smpt.zoho.com"
        self.smtp_port = 587

    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        plain_text_body: str = None,  # type: ignore
        attachments: List[str] = [],
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
    ) -> dict:
        """Send HTML email with proper rendering"""
        result = {"success": False, "message": "", "to": to, "subject": subject}

        try:
            # Create the root message
            msg = MIMEMultipart("mixed")
            msg["From"] = self.email
            msg["To"] = to if isinstance(to, str) else ", ".join(to)
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
            if bcc:
                msg["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

            # Create alternative part for HTML and plain text
            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)

            if plain_text_body is None:
                import re

                plain_text_body = re.sub("<[^<]+?>", "", html_body)

            msg_text = MIMEText(plain_text_body, "plain", "utf-8")
            msg_alternative.attach(msg_text)

            msg_html = MIMEText(html_body, "html", "utf-8")
            msg_alternative.attach(msg_html)

            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
                        print(f"  → Attached: {os.path.basename(file_path)}")

            # Build recipient list
            recipients = []
            if isinstance(to, str):
                recipients.append(to)
            else:
                recipients.extend(to)
            if cc:
                recipients.extend([cc] if isinstance(cc, str) else cc)
            if bcc:
                recipients.extend([bcc] if isinstance(bcc, str) else bcc)

            # --- FIX: Proper connection lifecycle for Port 587 ---
            logger.info(f"Connecting to {self.smtp_server}:{self.smtp_port}...")
            logger.info(f"Using {self.email} and {self.password}")
            with smtplib.SMTP_SSL("204.141.42.56", 465) as server:
                server.ehlo()
                logger.info("Send initial handshake identifying your client")
                # server.starttls()
                logger.info("Secure the unencrypted connection stream")
                server.ehlo()
                logger.info("Re-identify over the secure TLS channel")

                print("Authenticating...")
                server.login(self.email, self.password)

                print("Sending email...")
                server.sendmail(self.email, recipients, msg.as_string())

            result["success"] = True
            result["message"] = "Email sent successfully"
            print(f"✓ Email sent to {to}")

        except Exception as e:
            result["message"] = f"Failed to send: {str(e)}"
            print(f"✗ Error: {e}")
            raise

        return result

    def _attach_file(self, msg, file_path):
        """Attach a file to the message"""
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)
