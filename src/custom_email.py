#!/usr/bin/env python3

import os
import smtplib
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from typing import List, Union, Optional
from email.mime.multipart import MIMEMultipart


class ZohoEmailer:
    """Enhanced Zoho email sender with proper HTML support"""

    MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.smtp_server = "smtp.zoho.com"
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
        """
        Send HTML email with proper rendering

        CRITICAL: This creates a multipart/alternative message which is
        required for HTML emails to display correctly in all email clients

        Args:
            to: Recipient email(s)
            subject: Email subject
            html_body: HTML content (will render as designed)
            plain_text_body: Fallback plain text (optional, auto-generated if not provided)
            attachments: List of file paths
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            dict with status and details
        """
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

            # Add plain text version (fallback for clients that don't support HTML)
            if plain_text_body is None:
                # Auto-generate plain text from HTML (simple strip)
                import re

                plain_text_body = re.sub("<[^<]+?>", "", html_body)

            msg_text = MIMEText(plain_text_body, "plain", "utf-8")
            msg_alternative.attach(msg_text)

            # Add HTML version (this is what will be displayed)
            msg_html = MIMEText(html_body, "html", "utf-8")
            msg_alternative.attach(msg_html)

            # Attach files if provided
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

            # Send email
            print(f"Connecting to {self.smtp_server}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
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


if __name__ == "__main__":
    from decouple import config

    email_username = str(config("EMAIL_USERNAME"))
    email_password = str(config("EMAIL_PASSWORD"))
    mailer = ZohoDocumentMailer(email=email_username, password=email_password)

    # Example 1: Send single document with validation
    print("\n=== Sending Single Document ===")
    result = mailer.send_documents(
        to="franklinfidelugwuowo@gmail.com",
        subject="Project Proposal",
        body="Please review the attached proposal.",
        documents=["assets/media/certificate_template.png"],
    )
    print(f"Status: {result['message']}\n")
