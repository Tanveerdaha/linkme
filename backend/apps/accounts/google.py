"""Google OAuth helpers for LinkMe (authorization-code + ID-token verify)."""

from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from apps.accounts.services import AccountServiceError

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


@dataclass(frozen=True)
class GoogleIdentity:
    google_id: str
    email: str
    first_name: str
    last_name: str
    picture: str
    full_name: str


def _google_client_config() -> tuple[str, str, str]:
    client_id = (getattr(settings, "GOOGLE_CLIENT_ID", None) or "").strip()
    client_secret = (getattr(settings, "GOOGLE_CLIENT_SECRET", None) or "").strip()
    redirect_uri = (getattr(settings, "GOOGLE_REDIRECT_URI", None) or "").strip()
    if not client_id or not client_secret or not redirect_uri:
        raise AccountServiceError(
            "Google sign-in is not configured.",
            code="google_not_configured",
        )
    return client_id, client_secret, redirect_uri


def _identity_from_idinfo(idinfo: dict) -> GoogleIdentity:
    if idinfo.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    email = (idinfo.get("email") or "").strip().lower()
    google_sub = (idinfo.get("sub") or "").strip()
    if not email or not google_sub:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    if idinfo.get("email_verified") is False:
        raise AccountServiceError(
            "Google email is not verified.",
            code="unverified_google_email",
        )

    return GoogleIdentity(
        google_id=google_sub,
        email=email,
        first_name=(idinfo.get("given_name") or "").strip()[:150],
        last_name=(idinfo.get("family_name") or "").strip()[:150],
        picture=(idinfo.get("picture") or "").strip(),
        full_name=(idinfo.get("name") or "").strip(),
    )


def verify_google_id_token(token: str) -> GoogleIdentity:
    """Verify a Google ID token server-side."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    client_id = (getattr(settings, "GOOGLE_CLIENT_ID", None) or "").strip()
    if not client_id:
        raise AccountServiceError(
            "Google sign-in is not configured.",
            code="google_not_configured",
        )

    raw = (token or "").strip()
    if not raw:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            raw,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        ) from exc

    return _identity_from_idinfo(idinfo)


def exchange_authorization_code(code: str) -> GoogleIdentity:
    """
    Exchange a frontend-received authorization code for Google tokens.

    The client secret never leaves the backend. The ID token from Google is
    then verified before any user data is trusted.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    client_id, client_secret, redirect_uri = _google_client_config()
    raw_code = (code or "").strip()
    if not raw_code:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    try:
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": raw_code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="google_exchange_failed",
        ) from exc

    payload = {}
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400 or "error" in payload:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    raw_id_token = (payload.get("id_token") or "").strip()
    if not raw_id_token:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        ) from exc

    return _identity_from_idinfo(idinfo)
