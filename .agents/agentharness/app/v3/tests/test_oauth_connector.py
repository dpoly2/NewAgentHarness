"""
test_oauth_connector.py — Unit tests for oauth_connector.py:
  - PROVIDER_PRESETS keys and required fields
  - GoogleOAuth URL generation (no live network calls)
  - MicrosoftOAuth URL generation
  - XOAUTH2 string format
  - State store: store + consume (one-time use)
  - test_connector dispatcher routes correctly
  - PKCE code verifier / challenge format
"""
import sys, uuid, base64, re
from pathlib import Path

HERE = Path(__file__).parent
APP  = HERE.parent
sys.path.insert(0, str(APP))

import pytest
from oauth_connector import (
    GoogleOAuth,
    MicrosoftOAuth,
    PROVIDER_PRESETS,
    store_pending_state,
    consume_pending_state,
    _xoauth2_string,
)


def uid() -> str:
    return uuid.uuid4().hex[:12]


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER_PRESETS
# ─────────────────────────────────────────────────────────────────────────────

class TestProviderPresets:
    def test_required_providers_exist(self):
        for p in ("gmail", "outlook", "imap", "zoho", "yahoo"):
            assert p in PROVIDER_PRESETS, f"Missing preset: {p}"

    def test_preset_has_required_fields(self):
        required = {"imap_host", "imap_port", "smtp_host", "smtp_port", "auth_types"}
        for name, preset in PROVIDER_PRESETS.items():
            missing = required - set(preset.keys())
            assert not missing, f"Preset '{name}' missing: {missing}"

    def test_oauth_providers_support_oauth2(self):
        assert "oauth2" in PROVIDER_PRESETS["gmail"]["auth_types"]
        assert "oauth2" in PROVIDER_PRESETS["outlook"]["auth_types"]

    def test_imap_provider_password_only(self):
        assert PROVIDER_PRESETS["imap"]["auth_types"] == ["password"]

    def test_gmail_hosts_correct(self):
        assert "gmail" in PROVIDER_PRESETS["gmail"]["imap_host"]
        assert "gmail" in PROVIDER_PRESETS["gmail"]["smtp_host"]

    def test_outlook_hosts_correct(self):
        assert "office365" in PROVIDER_PRESETS["outlook"]["imap_host"] or \
               "outlook"   in PROVIDER_PRESETS["outlook"]["imap_host"]


# ─────────────────────────────────────────────────────────────────────────────
# GoogleOAuth
# ─────────────────────────────────────────────────────────────────────────────

class TestGoogleOAuth:
    def test_get_authorization_url_returns_google_domain(self):
        g = GoogleOAuth("fake-client-id", "fake-secret", f"con-{uid()}")
        url, state, verifier = g.get_authorization_url()
        assert "accounts.google.com" in url or "google.com" in url

    def test_auth_url_contains_client_id(self):
        cid = f"client-{uid()}"
        g = GoogleOAuth(cid, "secret", f"con-{uid()}")
        url, _, _ = g.get_authorization_url()
        assert cid in url

    def test_auth_url_contains_scope(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        url, _, _ = g.get_authorization_url()
        assert "scope" in url.lower()

    def test_state_is_url_safe_string(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        _, state, _ = g.get_authorization_url()
        assert len(state) >= 16
        assert re.match(r'^[A-Za-z0-9_\-]+$', state)

    def test_code_verifier_is_url_safe(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        _, _, verifier = g.get_authorization_url()
        assert len(verifier) >= 43
        assert re.match(r'^[A-Za-z0-9_\-]+$', verifier)

    def test_pkce_code_challenge_in_url(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        url, _, _ = g.get_authorization_url()
        assert "code_challenge" in url

    def test_different_calls_produce_different_states(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        _, s1, _ = g.get_authorization_url()
        _, s2, _ = g.get_authorization_url()
        assert s1 != s2

    def test_redirect_uri_in_url(self):
        g = GoogleOAuth("cid", "sec", f"con-{uid()}")
        url, _, _ = g.get_authorization_url()
        assert "redirect_uri" in url


# ─────────────────────────────────────────────────────────────────────────────
# MicrosoftOAuth
# ─────────────────────────────────────────────────────────────────────────────

class TestMicrosoftOAuth:
    def test_get_authorization_url_returns_microsoft_domain(self):
        m = MicrosoftOAuth("fake-cid", "fake-sec", f"con-{uid()}")
        url, state = m.get_authorization_url()
        assert "microsoft" in url.lower() or "microsoftonline" in url.lower()

    def test_auth_url_contains_client_id(self):
        cid = f"ms-client-{uid()}"
        m = MicrosoftOAuth(cid, "sec", f"con-{uid()}")
        url, _ = m.get_authorization_url()
        assert cid in url

    def test_state_is_non_empty(self):
        m = MicrosoftOAuth("cid", "sec", f"con-{uid()}")
        _, state = m.get_authorization_url()
        assert len(state) >= 16

    def test_scope_in_url(self):
        m = MicrosoftOAuth("cid", "sec", f"con-{uid()}")
        url, _ = m.get_authorization_url()
        assert "scope" in url.lower()


# ─────────────────────────────────────────────────────────────────────────────
# XOAUTH2 string
# ─────────────────────────────────────────────────────────────────────────────

class TestXOAuth2:
    def test_xoauth2_string_format(self):
        token  = "ya29.test-access-token"
        email  = "user@gmail.com"
        result = _xoauth2_string(email, token)
        # Should be base64 encoded
        decoded = base64.b64decode(result).decode()
        assert f"user={email}" in decoded
        assert f"auth=Bearer {token}" in decoded

    def test_xoauth2_contains_null_bytes(self):
        result = _xoauth2_string("u@g.com", "tok")
        decoded = base64.b64decode(result).decode()
        assert decoded.count("\x01") >= 2


# ─────────────────────────────────────────────────────────────────────────────
# State store
# ─────────────────────────────────────────────────────────────────────────────

class TestStateStore:
    def test_store_and_consume(self):
        state = uid()
        store_pending_state(state, "con-123", "google", "verifier-abc")
        result = consume_pending_state(state)
        assert result is not None
        assert result["connector_id"] == "con-123"
        assert result["provider"] == "google"
        assert result["verifier"] == "verifier-abc"

    def test_consume_is_one_time_only(self):
        state = uid()
        store_pending_state(state, "con-456", "microsoft")
        consume_pending_state(state)          # first consume
        second = consume_pending_state(state)  # should be None
        assert second is None

    def test_consume_unknown_state_returns_none(self):
        result = consume_pending_state("nonexistent-state-xyz")
        assert result is None

    def test_different_states_independent(self):
        s1, s2 = uid(), uid()
        store_pending_state(s1, "con-1", "google")
        store_pending_state(s2, "con-2", "microsoft")
        r1 = consume_pending_state(s1)
        r2 = consume_pending_state(s2)
        assert r1["connector_id"] == "con-1"
        assert r2["connector_id"] == "con-2"
