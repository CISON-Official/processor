"""
zoho_campaign_mailer.py
-----------------------
Send campaign emails via the Zoho Campaigns Email API v2 (Transmission API).

Authentication flow
-------------------
Zoho uses OAuth 2.0. Access tokens expire after 1 hour; this client
automatically refreshes them using the stored refresh token.

One-time setup (do this once in a browser / Postman):
1. Register an app at https://api-console.zoho.com
2. Choose "Server-based Application"
3. Note your Client ID and Client Secret
4. Visit this URL to get a grant code:
   https://accounts.zoho.com/oauth/v2/auth
     ?scope=ZohoCampaigns.emailapi.ALL
     &client_id=YOUR_CLIENT_ID
     &response_type=code
     &access_type=offline
     &redirect_uri=YOUR_REDIRECT_URI
5. Exchange the grant code for tokens (POST to accounts.zoho.com/oauth/v2/token)
   — see get_initial_tokens() helper below, or do it in Postman.
6. Store the refresh_token in your .env / environment.

Docs:
  Transmission API  : https://www.zoho.com/campaigns/help/emailapi/transmission/send-email.html
  OAuth             : https://www.zoho.com/accounts/protocol/oauth.html
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from decouple import config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ---------------------------------------------------------------------------
# Region → Accounts URL map  (pick the one that matches your Zoho account)
# ---------------------------------------------------------------------------
ACCOUNTS_URLS: Dict[str, str] = {
    "com": "https://accounts.zoho.com",
    "eu": "https://accounts.zoho.eu",
    "in": "https://accounts.zoho.in",
    "au": "https://accounts.zoho.com.au",
    "jp": "https://accounts.zoho.jp",
    "ca": "https://accounts.zohocloud.ca",
}

# Transmission API endpoint (same for all regions)
TRANSMISSION_URL = "https://campaigns.zoho.com/emailapi/v2/transmission"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Recipient:
    address: str
    name: str = ""
    merge_data: Dict[str, str] = field(default_factory=dict)
    additional_data: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"address": self.address}
        if self.name:
            d["name"] = self.name
        if self.merge_data:
            d["merge_data"] = self.merge_data
        if self.additional_data:
            d["additional_data"] = self.additional_data
        return d


@dataclass
class Attachment:
    """File to attach.  Pass either file_path or raw bytes + filename."""

    filename: str
    data: bytes  # raw bytes; will be base64-encoded automatically

    @classmethod
    def from_path(cls, path: str | Path) -> "Attachment":
        p = Path(path)
        return cls(filename=p.name, data=p.read_bytes())

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.filename,
            "data": base64.b64encode(self.data).decode(),
        }


@dataclass
class CampaignEmail:
    """Everything needed to send one transmission."""

    transmission_name: str  # unique label for this send
    from_address: str
    from_name: str
    subject: str

    # Supply either `recipients` (inline list) or `recipient_list_id` (saved list)
    recipients: List[Recipient] = field(default_factory=list)
    recipient_list_id: Optional[str] = None

    html_body: Optional[str] = None
    text_body: Optional[str] = None
    template_id: Optional[str] = None  # pre-saved Zoho template

    reply_to: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)

    # Delivery options
    open_tracking: bool = True
    click_tracking: bool = True
    schedule_at_ms: Optional[int] = None  # Unix epoch in milliseconds

    def to_payload(self) -> Dict[str, Any]:
        if not self.recipients and not self.recipient_list_id:
            raise ValueError("Supply either 'recipients' or 'recipient_list_id'")
        if not self.html_body and not self.text_body and not self.template_id:
            raise ValueError("Supply html_body, text_body, or template_id")

        payload: Dict[str, Any] = {
            "transmission_name": self.transmission_name,
            "content": {
                "from": {
                    "address": self.from_address,
                    "name": self.from_name,
                },
                "subject": self.subject,
            },
            "options": {
                "open_tracking": "enabled" if self.open_tracking else "disabled",
                "click_tracking": "enabled" if self.click_tracking else "disabled",
            },
        }

        # Recipients
        if self.recipient_list_id:
            payload["recipient_list_id"] = self.recipient_list_id
        else:
            payload["recipients"] = [r.to_dict() for r in self.recipients]

        # Content
        content = payload["content"]
        if self.html_body:
            content["html"] = self.html_body
        if self.text_body:
            content["text"] = self.text_body
        if self.template_id:
            content["template_id"] = self.template_id
        if self.reply_to:
            content["reply_to"] = self.reply_to
        if self.attachments:
            content["attachments"] = [a.to_dict() for a in self.attachments]

        # Scheduling
        if self.schedule_at_ms:
            payload["options"]["schedule_at"] = self.schedule_at_ms

        return payload


# ---------------------------------------------------------------------------
# OAuth2 token manager
# ---------------------------------------------------------------------------


class ZohoTokenManager:
    """
    Manages access + refresh tokens for a Zoho OAuth2 app.

    Tokens are cached in a local JSON file so they survive restarts.
    The access token is refreshed automatically when it is within
    60 seconds of expiry.
    """

    TOKEN_ENDPOINT = "/oauth/v2/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        region: str = "com",
        token_cache_path: str | Path = ".zoho_tokens.json",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.accounts_url = ACCOUNTS_URLS[region]
        self.token_cache_path = Path(token_cache_path)
        self.redirect_url = "https://my.cison.org.ng/members/wp-admin/admin.php?page=zmail-integ-settings"

        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

        self._load_cache()

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _load_cache(self) -> None:
        if self.token_cache_path.exists():
            try:
                data = json.loads(self.token_cache_path.read_text())
                self._access_token = data.get("access_token")
                self._expires_at = float(data.get("expires_at", 0))
                logger.debug("Loaded cached token (expires at %s)", self._expires_at)
            except Exception as exc:
                logger.warning("Could not read token cache: %s", exc)

    def _save_cache(self) -> None:
        try:
            self.token_cache_path.write_text(
                json.dumps(
                    {
                        "access_token": self._access_token,
                        "expires_at": self._expires_at,
                    }
                )
            )
        except Exception as exc:
            logger.warning("Could not write token cache: %s", exc)

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        logger.info("Refreshing Zoho access token …")

        monkey = f"https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCampaigns.contact.ALL,ZohoCampaigns.campaign.ALL,ZohoCampaigns.emailapi.ALL&client_id={self.client_id}&response_type=code&access_type=offline&redirect_uri={self.redirect_url}&prompt=consent"
        print(monkey)
        resp = requests.post(
            f"{self.accounts_url}{self.TOKEN_ENDPOINT}",
            params={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        print(data)
        if "access_token" not in data:
            raise RuntimeError(f"Token refresh failed: {data}")

        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.time() + expires_in - 60  # 60s safety buffer
        self._save_cache()
        logger.info("Access token refreshed (valid for ~%ds)", expires_in)

    @property
    def access_token(self) -> str:
        print(self._access_token, self._expires_at)
        if not self._access_token or time.time() >= self._expires_at:
            self._refresh()
        return self._access_token  # type: ignore[return-value]
        # return "1000.ef6a2cb6d028165d18f53ac8eef71e07.abb4dd11fd2c7370244a47281e9c6892"

    # ------------------------------------------------------------------
    # One-time helper: exchange a grant code for tokens
    # ------------------------------------------------------------------

    @classmethod
    def get_initial_tokens(
        cls,
        client_id: str,
        client_secret: str,
        grant_code: str,
        redirect_uri: str,
        region: str = "com",
    ) -> Dict[str, str]:
        """
        Exchange a one-time grant code for access + refresh tokens.
        Call this once; store the returned refresh_token securely.
        """
        accounts_url = ACCOUNTS_URLS[region]
        resp = requests.post(
            f"{accounts_url}/oauth/v2/token",
            params={
                "code": grant_code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Campaign mailer client
# ---------------------------------------------------------------------------


class ZohoCampaignMailer:
    """
    High-level client for Zoho Campaigns Email API v2.

    Usage
    -----
    mailer = ZohoCampaignMailer.from_env()   # reads env vars
    result = mailer.send(campaign_email)
    print(result)
    """

    def __init__(self, token_manager: ZohoTokenManager):
        self.tokens = token_manager
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls, region: str = "in") -> "ZohoCampaignMailer":
        """
        Build from environment variables:
          ZOHO_CLIENT_ID
          ZOHO_CLIENT_SECRET
          ZOHO_REFRESH_TOKEN
        """
        # print(os.environ)
        client_id = config("ZOHO_CLIENT_ID")
        client_secret = config("ZOHO_CLIENT_SECRET")
        refresh_token = config("ZOHO_REFRESH_TOKEN")
        manager = ZohoTokenManager(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            region=region,
        )
        return cls(manager)

    # ------------------------------------------------------------------
    # Core send
    # ------------------------------------------------------------------

    def send(self, campaign: CampaignEmail) -> Dict[str, Any]:
        """
        Send a transmission. Returns the parsed JSON response from Zoho.
        Raises requests.HTTPError on HTTP-level failures.
        """
        payload = campaign.to_payload()
        headers = {
            "Authorization": f"Bearer {self.tokens.access_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Sending transmission '%s' to %d recipients …",
            campaign.transmission_name,
            len(campaign.recipients) if campaign.recipients else -1,
        )

        resp = self.session.post(
            TRANSMISSION_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            logger.error("HTTP error: %s  body: %s", exc, resp.text)
            raise

        data = resp.json()
        logger.info(
            "Transmission sent — accepted: %s  rejected: %s  id: %s",
            data.get("accepted_recipients"),
            data.get("rejected_recipients"),
            data.get("transmission_id"),
        )
        return data

    def send_to_list(
        self,
        *,
        transmission_name: str,
        from_address: str,
        from_name: str,
        subject: str,
        html_body: str,
        recipient_list_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Convenience wrapper for sending to a saved Zoho recipient list."""
        campaign = CampaignEmail(
            transmission_name=transmission_name,
            from_address=from_address,
            from_name=from_name,
            subject=subject,
            html_body=html_body,
            recipient_list_id=recipient_list_id,
            **kwargs,
        )
        return self.send(campaign)


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # ONE-TIME: exchange a grant code for tokens (run once, save refresh_token)
    # -----------------------------------------------------------------------
    # tokens = ZohoTokenManager.get_initial_tokens(
    #     client_id="YOUR_CLIENT_ID",
    #     client_secret="YOUR_CLIENT_SECRET",
    #     grant_code="GRANT_CODE_FROM_BROWSER",
    #     redirect_uri="https://yourapp.com/callback",
    #     region="com",
    # )
    # print("Refresh token:", tokens["refresh_token"])
    # -----------------------------------------------------------------------

    # Build client from environment variables
    mailer = ZohoCampaignMailer.from_env(region="com")

    # --- Example 1: inline recipients with merge tags ---
    campaign = CampaignEmail(
        transmission_name="welcome_batch_001",
        from_address="support@cison.org.ng",
        from_name="Chactered Institute of Statisticians of Nigeria",
        subject="Welcome, $[first_name|Friend]$!",
        html_body="""
            <html><body>
              <p>Hi $[first_name|there]$,</p>
              <p>Welcome to our platform! We're thrilled to have you.</p>
              <p>
                <a href="https://yourapp.com/unsubscribe"
                   data-zcea-unsubscribe="1">Unsubscribe</a>
              </p>
            </body></html>
        """,
        recipients=[
            Recipient(
                address="franklinfidelugwuowo@gmail.com",
                name="Franklin",
                merge_data={"first_name": "Franklin"},
            ),
            Recipient(
                address="Sysadmin@cison.org.ng",
                name="Sys Admin",
                merge_data={"first_name": "Sys Admin"},
            ),
        ],
        reply_to="support@cison.org.ng",
    )

    result = mailer.send(campaign)
    print(json.dumps(result, indent=2))

    # --- Example 2: send to a saved Zoho recipient list ---
    result2 = mailer.send_to_list(
        transmission_name="newsletter_april_2026",
        from_address="support@cison.org.ng",
        from_name="Chartered Institute of Statisticians of Nigeria",
        subject="April 2026 — What's new",
        html_body="<html><body><p>Here's what happened this month…</p></body></html>",
        recipient_list_id="8000000097065",  # from Zoho Campaigns dashboard
    )
    print(json.dumps(result2, indent=2))

    # --- Example 3: send with an attachment ---
    attachment = Attachment.from_path("/tmp/report.pdf")
    campaign_with_attachment = CampaignEmail(
        transmission_name="monthly_report",
        from_address="Support",
        from_name="Reports Team",
        subject="Your April report",
        html_body="<p>Please find your report attached.</p>",
        recipients=[
            Recipient(address="sysadmin@cison.org.ng", name="Manager"),
            Recipient(address="franklinfidelugwuowo@gmail.com", name="CEO"),
        ],
        attachments=[attachment],
    )
    result3 = mailer.send(campaign_with_attachment)
    print(json.dumps(result3, indent=2))
