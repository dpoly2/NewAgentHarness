"""
oauth_connector.py — ArchonHub Email OAuth Integration
=======================================================
Proper OAuth2 flows for Gmail and Outlook/Microsoft 365.

Google Gmail
------------
  Flow  : Authorization Code (web redirect to localhost callback)
  Auth  : XOAUTH2 over IMAP (imap.gmail.com:993) + SMTP (smtp.gmail.com:587)
  Tokens: access_token (1h) + refresh_token (long-lived)
  Scopes: https://mail.google.com/
  Prereq: Google Cloud Console project → OAuth 2.0 Client ID (Web app)
          Redirect URI: http://localhost:8765/api/connectors/oauth/google/callback

Microsoft Outlook / Office 365
-------------------------------
  Flow  : Authorization Code via MSAL (or device-code fallback)
  Auth  : XOAUTH2 over IMAP (outlook.office365.com:993) + SMTP (smtp.office365.com:587)
  Tokens: access_token (~1h) + refresh_token (long-lived with offline_access)
  Scopes: https://outlook.office.com/IMAP.AccessAsUser.All
          https://outlook.office.com/SMTP.Send offline_access email openid
  Prereq: Azure App Registration → client_id (+ optional client_secret)
          Redirect URI: http://localhost:8765/api/connectors/oauth/microsoft/callback

IMAP / SMTP Password (plain)
-----------------------------
  Standard username+password auth — works for any IMAP provider:
  Zoho, Yahoo (App Password), ProtonMail Bridge, custom corporate IMAP, etc.

Credentials stored in email_connectors.credentials JSON:
  {
    "access_token":  "...",
    "refresh_token": "...",
    "expires_at":    1234567890,   # Unix timestamp
    "token_type":    "Bearer",
    "email":         "user@gmail.com"
  }
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import imaplib
import json
import os
import secrets
import smtplib
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import sys
HERE = Path(__file__).parent
for _p in [HERE, HERE.parent.parent, HERE.parent.parent.parent]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from ah_logging import get_logger
    logger = get_logger("oauth_connector")
except Exception:
    import logging
    logger = logging.getLogger("oauth_connector")

# ── Constants ─────────────────────────────────────────────────────────────────

REDIRECT_BASE = os.environ.get("ARCHONHUB_REDIRECT_BASE", "http://localhost:8765")

# Google
GOOGLE_AUTH_URL   = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_SCOPES     = "https://mail.google.com/ email profile"
GOOGLE_IMAP_HOST  = "imap.gmail.com"
GOOGLE_IMAP_PORT  = 993
GOOGLE_SMTP_HOST  = "smtp.gmail.com"
GOOGLE_SMTP_PORT  = 587
GOOGLE_REDIRECT   = f"{REDIRECT_BASE}/api/connectors/oauth/google/callback"

# Microsoft
MS_AUTH_URL   = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL  = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_SCOPES     = (
    "https://outlook.office.com/IMAP.AccessAsUser.All "
    "https://outlook.office.com/SMTP.Send "
    "offline_access email openid"
)
MS_IMAP_HOST  = "outlook.office365.com"
MS_IMAP_PORT  = 993
MS_SMTP_HOST  = "smtp.office365.com"
MS_SMTP_PORT  = 587
MS_REDIRECT   = f"{REDIRECT_BASE}/api/connectors/oauth/microsoft/callback"

# Token buffer — refresh if expiring within 5 minutes
TOKEN_REFRESH_BUFFER = 300


# ── PKCE helpers ─────────────────────────────────────────────────────────────

def _pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) for PKCE S256."""
    verifier  = secrets.token_urlsafe(64)
    digest    = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _xoauth2_string(email: str, access_token: str) -> str:
    """Build the XOAUTH2 base64 string for IMAP/SMTP AUTH."""
    raw = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(raw.encode()).decode()


# ── Token storage helpers ─────────────────────────────────────────────────────

def _creds_from_db(connector_id: str) -> dict:
    try:
        import hub_db
        c = hub_db.get_connector(connector_id)
        if not c:
            return {}
        raw = c.get("credentials", "{}")
        return json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception:
        return {}


def _save_token(connector_id: str, token_data: dict) -> None:
    try:
        import hub_db
        hub_db.update_connector(connector_id, credentials=json.dumps(token_data))
    except Exception as e:
        logger.error("save_token failed: %s", e)


def is_token_valid(creds: dict) -> bool:
    """Return True if access_token exists and is not about to expire."""
    if not creds.get("access_token"):
        return False
    exp = creds.get("expires_at", 0)
    return (time.time() + TOKEN_REFRESH_BUFFER) < exp


def token_status(connector_id: str) -> str:
    """Return human-readable token status for a connector."""
    creds = _creds_from_db(connector_id)
    if not creds.get("access_token"):
        return "not_authorized"
    exp = creds.get("expires_at", 0)
    remaining = int(exp - time.time())
    if remaining <= 0:
        return "expired"
    if remaining < TOKEN_REFRESH_BUFFER:
        return "expiring_soon"
    return "valid"


# ── Google OAuth2 ─────────────────────────────────────────────────────────────

class GoogleOAuth:
    """
    Handles the full Google OAuth2 Authorization Code flow.

    Usage:
        g = GoogleOAuth(client_id, client_secret, connector_id)
        url, state, verifier = g.get_authorization_url()
        # redirect user to url ...
        # on callback with code + state:
        token = g.exchange_code(code, verifier)
        # token is saved to DB automatically
    """

    def __init__(self, client_id: str, client_secret: str,
                 connector_id: str | None = None):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.connector_id  = connector_id

    def get_authorization_url(self) -> tuple[str, str, str]:
        """
        Returns (auth_url, state, code_verifier).
        State and verifier must be stored by the caller and verified on callback.
        """
        state    = secrets.token_urlsafe(24)
        verifier, challenge = _pkce_pair()
        params = {
            "client_id":             self.client_id,
            "redirect_uri":          GOOGLE_REDIRECT,
            "response_type":         "code",
            "scope":                 GOOGLE_SCOPES,
            "access_type":           "offline",
            "prompt":                "consent",          # force refresh_token
            "state":                 state,
            "code_challenge":        challenge,
            "code_challenge_method": "S256",
        }
        url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url, state, verifier

    def exchange_code(self, code: str, code_verifier: str) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        data = urllib.parse.urlencode({
            "code":          code,
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri":  GOOGLE_REDIRECT,
            "grant_type":    "authorization_code",
            "code_verifier": code_verifier,
        }).encode()
        req = urllib.request.Request(
            GOOGLE_TOKEN_URL, data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read())
        token["expires_at"] = time.time() + token.get("expires_in", 3600)
        if self.connector_id:
            _save_token(self.connector_id, token)
        return token

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Use refresh_token to get a new access_token."""
        data = urllib.parse.urlencode({
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type":    "refresh_token",
        }).encode()
        req = urllib.request.Request(
            GOOGLE_TOKEN_URL, data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read())
        token["refresh_token"] = refresh_token  # preserve existing refresh_token
        token["expires_at"]    = time.time() + token.get("expires_in", 3600)
        return token

    def get_valid_token(self, connector_id: str | None = None) -> str:
        """
        Return a valid access_token for this connector.
        Auto-refreshes if expired or about to expire.
        """
        cid   = connector_id or self.connector_id
        creds = _creds_from_db(cid) if cid else {}
        if is_token_valid(creds):
            return creds["access_token"]
        refresh = creds.get("refresh_token", "")
        if not refresh:
            raise RuntimeError("No refresh_token — user must re-authorize")
        token = self.refresh_access_token(refresh)
        if cid:
            _save_token(cid, token)
        return token["access_token"]

    def revoke(self, connector_id: str | None = None) -> bool:
        cid   = connector_id or self.connector_id
        creds = _creds_from_db(cid) if cid else {}
        token = creds.get("access_token") or creds.get("refresh_token", "")
        if not token:
            return True
        try:
            url = GOOGLE_REVOKE_URL + "?" + urllib.parse.urlencode({"token": token})
            urllib.request.urlopen(url, timeout=10)
            if cid:
                _save_token(cid, {})
            return True
        except Exception as e:
            logger.warning("Google revoke failed: %s", e)
            return False

    @staticmethod
    def test_imap(email: str, access_token: str) -> tuple[bool, str]:
        """Test IMAP connection using XOAUTH2. Returns (ok, message)."""
        try:
            imap = imaplib.IMAP4_SSL(GOOGLE_IMAP_HOST, GOOGLE_IMAP_PORT)
            auth_str = _xoauth2_string(email, access_token)
            imap.authenticate("XOAUTH2", lambda x: auth_str)
            imap.select("INBOX")
            _, msgs = imap.search(None, "ALL")
            count = len(msgs[0].split()) if msgs[0] else 0
            imap.logout()
            return True, f"Connected. {count} messages in INBOX."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def test_smtp(email: str, access_token: str) -> tuple[bool, str]:
        """Test SMTP connection using XOAUTH2."""
        try:
            smtp = smtplib.SMTP(GOOGLE_SMTP_HOST, GOOGLE_SMTP_PORT, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            auth_str = _xoauth2_string(email, access_token)
            smtp.docmd("AUTH", f"XOAUTH2 {auth_str}")
            smtp.quit()
            return True, "SMTP XOAUTH2 authenticated."
        except Exception as e:
            return False, str(e)


# ── Microsoft OAuth2 (MSAL) ───────────────────────────────────────────────────

class MicrosoftOAuth:
    """
    Handles Microsoft OAuth2 Authorization Code flow.
    Uses MSAL if available, falls back to raw urllib.

    Usage:
        m = MicrosoftOAuth(client_id, client_secret, connector_id)
        url, state = m.get_authorization_url()
        # redirect user ...
        # on callback:
        token = m.exchange_code(code)
    """

    def __init__(self, client_id: str, client_secret: str = "",
                 connector_id: str | None = None,
                 tenant: str = "common"):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.connector_id  = connector_id
        self.tenant        = tenant
        self._msal_app     = None

    def _get_msal_app(self):
        if self._msal_app is not None:
            return self._msal_app
        try:
            import msal  # type: ignore
            if self.client_secret:
                self._msal_app = msal.ConfidentialClientApplication(
                    self.client_id,
                    authority=f"https://login.microsoftonline.com/{self.tenant}",
                    client_credential=self.client_secret,
                )
            else:
                self._msal_app = msal.PublicClientApplication(
                    self.client_id,
                    authority=f"https://login.microsoftonline.com/{self.tenant}",
                )
            return self._msal_app
        except ImportError:
            return None

    def get_authorization_url(self) -> tuple[str, str]:
        """Returns (auth_url, state)."""
        state  = secrets.token_urlsafe(24)
        scopes = MS_SCOPES.split()
        app    = self._get_msal_app()
        if app is not None:
            try:
                result = app.get_authorization_request_url(
                    scopes=scopes,
                    redirect_uri=MS_REDIRECT,
                    state=state,
                )
                return result, state
            except Exception:
                pass
        # Raw fallback
        params = {
            "client_id":     self.client_id,
            "response_type": "code",
            "redirect_uri":  MS_REDIRECT,
            "scope":         MS_SCOPES,
            "state":         state,
            "response_mode": "query",
            "prompt":        "select_account",
        }
        url = (f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/authorize?"
               + urllib.parse.urlencode(params))
        return url, state

    def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        app = self._get_msal_app()
        scopes = MS_SCOPES.split()
        if app is not None:
            try:
                result = app.acquire_token_by_authorization_code(
                    code,
                    scopes=scopes,
                    redirect_uri=MS_REDIRECT,
                )
                if "access_token" in result:
                    result["expires_at"] = time.time() + result.get("expires_in", 3600)
                    if self.connector_id:
                        _save_token(self.connector_id, result)
                    return result
                raise RuntimeError(result.get("error_description", str(result)))
            except Exception as e:
                logger.warning("MSAL exchange failed, using raw: %s", e)

        # Raw fallback
        data = urllib.parse.urlencode({
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "code":          code,
            "redirect_uri":  MS_REDIRECT,
            "grant_type":    "authorization_code",
            "scope":         MS_SCOPES,
        }).encode()
        req = urllib.request.Request(
            f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read())
        token["expires_at"] = time.time() + token.get("expires_in", 3600)
        if self.connector_id:
            _save_token(self.connector_id, token)
        return token

    def refresh_access_token(self, refresh_token: str) -> dict:
        app    = self._get_msal_app()
        scopes = MS_SCOPES.split()
        if app is not None:
            try:
                accounts = app.get_accounts()
                if accounts:
                    result = app.acquire_token_silent(scopes, account=accounts[0])
                    if result and "access_token" in result:
                        result["expires_at"] = time.time() + result.get("expires_in", 3600)
                        return result
            except Exception:
                pass

        # Raw ROPC refresh
        data = urllib.parse.urlencode({
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type":    "refresh_token",
            "scope":         MS_SCOPES,
        }).encode()
        req = urllib.request.Request(
            f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read())
        token["expires_at"]    = time.time() + token.get("expires_in", 3600)
        token["refresh_token"] = token.get("refresh_token") or refresh_token
        return token

    def get_valid_token(self, connector_id: str | None = None) -> str:
        cid   = connector_id or self.connector_id
        creds = _creds_from_db(cid) if cid else {}
        if is_token_valid(creds):
            return creds["access_token"]
        refresh = creds.get("refresh_token", "")
        if not refresh:
            raise RuntimeError("No refresh_token — user must re-authorize")
        token = self.refresh_access_token(refresh)
        if cid:
            _save_token(cid, token)
        return token["access_token"]

    @staticmethod
    def test_imap(email: str, access_token: str) -> tuple[bool, str]:
        """Test IMAP XOAUTH2 for Microsoft."""
        try:
            imap = imaplib.IMAP4_SSL(MS_IMAP_HOST, MS_IMAP_PORT)
            auth_str = _xoauth2_string(email, access_token)
            imap.authenticate("XOAUTH2", lambda x: auth_str)
            imap.select("INBOX")
            _, msgs = imap.search(None, "ALL")
            count = len(msgs[0].split()) if msgs[0] else 0
            imap.logout()
            return True, f"Connected. {count} messages in INBOX."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def test_smtp(email: str, access_token: str) -> tuple[bool, str]:
        """Test SMTP XOAUTH2 for Microsoft."""
        try:
            smtp = smtplib.SMTP(MS_SMTP_HOST, MS_SMTP_PORT, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            auth_str = _xoauth2_string(email, access_token)
            smtp.docmd("AUTH", f"XOAUTH2 {auth_str}")
            smtp.quit()
            return True, "SMTP XOAUTH2 authenticated."
        except Exception as e:
            return False, str(e)

    def get_device_code_flow(self) -> dict:
        """
        Initiate device code flow (for CLI / headless environments).
        Returns flow dict with 'user_code' and 'verification_uri'.
        Caller should display these to the user, then call poll_device_code().
        """
        app = self._get_msal_app()
        if app is None:
            raise ImportError("msal not installed — pip install msal")
        flow = app.initiate_device_flow(scopes=MS_SCOPES.split())
        if "user_code" not in flow:
            raise RuntimeError(flow.get("error_description", "Device flow failed"))
        return flow

    def poll_device_code(self, flow: dict) -> dict:
        """Poll until user has completed device code auth. May block."""
        app = self._get_msal_app()
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(result.get("error_description", str(result)))
        result["expires_at"] = time.time() + result.get("expires_in", 3600)
        if self.connector_id:
            _save_token(self.connector_id, result)
        return result


# ── Plain IMAP/SMTP password auth ─────────────────────────────────────────────

def test_imap_password(host: str, port: int, username: str,
                       password: str) -> tuple[bool, str]:
    """Test plain IMAP login."""
    try:
        if port == 993:
            imap = imaplib.IMAP4_SSL(host, port)
        else:
            imap = imaplib.IMAP4(host, port)
        imap.login(username, password)
        imap.select("INBOX")
        _, msgs = imap.search(None, "ALL")
        count = len(msgs[0].split()) if msgs[0] else 0
        imap.logout()
        return True, f"Connected. {count} messages in INBOX."
    except Exception as e:
        return False, str(e)


def test_smtp_password(host: str, port: int, username: str,
                       password: str) -> tuple[bool, str]:
    """Test plain SMTP login."""
    try:
        smtp = smtplib.SMTP(host, port, timeout=10)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.quit()
        return True, "SMTP authenticated."
    except Exception as e:
        return False, str(e)


# ── Universal connector test dispatcher ──────────────────────────────────────

def test_connector(connector: dict) -> tuple[bool, str]:
    """
    Test any connector type. Returns (success, message).
    connector is a row dict from hub_db.list_connectors().
    """
    provider  = connector.get("provider", "imap")
    auth_type = connector.get("auth_type", "password")
    email     = connector.get("email_address", "")
    creds_raw = connector.get("credentials", "{}")
    creds     = json.loads(creds_raw) if isinstance(creds_raw, str) else (creds_raw or {})

    if provider == "gmail" and auth_type == "oauth2":
        client_id  = connector.get("oauth_client_id", "")
        client_sec = connector.get("oauth_client_secret", "")
        cid        = connector.get("id", "")
        if not creds.get("refresh_token"):
            return False, "Not authorized — click 'Authorize with Google'"
        g = GoogleOAuth(client_id, client_sec, cid)
        try:
            token = g.get_valid_token(cid)
        except Exception as e:
            return False, f"Token refresh failed: {e}"
        return GoogleOAuth.test_imap(email, token)

    if provider in ("outlook", "microsoft") and auth_type == "oauth2":
        client_id  = connector.get("oauth_client_id", "")
        client_sec = connector.get("oauth_client_secret", "")
        cid        = connector.get("id", "")
        if not creds.get("refresh_token"):
            return False, "Not authorized — click 'Authorize with Microsoft'"
        m = MicrosoftOAuth(client_id, client_sec, cid)
        try:
            token = m.get_valid_token(cid)
        except Exception as e:
            return False, f"Token refresh failed: {e}"
        return MicrosoftOAuth.test_imap(email, token)

    # Password / IMAP
    host     = connector.get("imap_host", "")
    port     = int(connector.get("imap_port") or 993)
    username = connector.get("username") or email
    password = creds.get("password", "")
    if not host:
        return False, "No IMAP host configured"
    return test_imap_password(host, port, username, password)


# ── OAuth state store (in-process, keyed by state token) ─────────────────────
# Stores pending OAuth flows so callback can retrieve verifier + connector_id

_pending_states: dict[str, dict] = {}  # state → {verifier, connector_id, provider}


def store_pending_state(state: str, connector_id: str, provider: str,
                        verifier: str = "") -> None:
    _pending_states[state] = {
        "connector_id": connector_id,
        "provider":     provider,
        "verifier":     verifier,
        "ts":           time.time(),
    }
    # Purge stale states (>10 min)
    cutoff = time.time() - 600
    for s in list(_pending_states):
        if _pending_states[s]["ts"] < cutoff:
            del _pending_states[s]


def consume_pending_state(state: str) -> dict | None:
    return _pending_states.pop(state, None)


# ── Provider config presets ───────────────────────────────────────────────────

PROVIDER_PRESETS = {
    "gmail": {
        "label":       "Gmail",
        "auth_types":  ["oauth2", "app_password"],
        "imap_host":   GOOGLE_IMAP_HOST,
        "imap_port":   GOOGLE_IMAP_PORT,
        "smtp_host":   GOOGLE_SMTP_HOST,
        "smtp_port":   GOOGLE_SMTP_PORT,
        "auth_note":   "OAuth2 recommended. App Password requires 2FA enabled in Google Account.",
        "oauth_note":  "Requires Google Cloud Console project with Gmail API enabled.",
        "help_url":    "https://console.cloud.google.com/apis/credentials",
    },
    "outlook": {
        "label":       "Outlook / Microsoft 365",
        "auth_types":  ["oauth2", "app_password"],
        "imap_host":   MS_IMAP_HOST,
        "imap_port":   MS_IMAP_PORT,
        "smtp_host":   MS_SMTP_HOST,
        "smtp_port":   MS_SMTP_PORT,
        "auth_note":   "OAuth2 recommended for Microsoft 365. App Password for legacy accounts.",
        "oauth_note":  "Requires Azure App Registration with IMAP/SMTP delegated permissions.",
        "help_url":    "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps",
    },
    "imap": {
        "label":       "Custom IMAP",
        "auth_types":  ["password"],
        "imap_host":   "",
        "imap_port":   993,
        "smtp_host":   "",
        "smtp_port":   587,
        "auth_note":   "Standard username + password. Use App Passwords where 2FA is enabled.",
        "oauth_note":  "",
        "help_url":    "",
    },
    "zoho": {
        "label":       "Zoho Mail",
        "auth_types":  ["password"],
        "imap_host":   "imap.zoho.com",
        "imap_port":   993,
        "smtp_host":   "smtp.zoho.com",
        "smtp_port":   587,
        "auth_note":   "Use Zoho App Password if 2FA is enabled.",
        "oauth_note":  "",
        "help_url":    "https://accounts.zoho.com/",
    },
    "yahoo": {
        "label":       "Yahoo Mail",
        "auth_types":  ["app_password"],
        "imap_host":   "imap.mail.yahoo.com",
        "imap_port":   993,
        "smtp_host":   "smtp.mail.yahoo.com",
        "smtp_port":   587,
        "auth_note":   "Yahoo requires an App Password. Regular password will not work.",
        "oauth_note":  "",
        "help_url":    "https://login.yahoo.com/account/security",
    },
}
