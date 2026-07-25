"""WhatsApp / message-service client for OTP delivery."""

from __future__ import annotations

import logging

import requests
from django.conf import settings

from apps.accounts.services import AccountServiceError

logger = logging.getLogger(__name__)


def send_whatsapp_message(*, phone_number: str, message: str) -> None:
    """
    Send a WhatsApp-style message via the configured message service.

    Uses WHATSAPP_API_URL and WHATSAPP_API_KEY from environment.
    """
    url = (getattr(settings, "WHATSAPP_API_URL", None) or "").strip()
    api_key = (getattr(settings, "WHATSAPP_API_KEY", None) or "").strip()
    if not url or not api_key:
        raise AccountServiceError(
            "WhatsApp messaging is not configured.",
            code="whatsapp_not_configured",
        )

    try:
        response = requests.post(
            url,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-App-Key": api_key,
            },
            json={
                "phone_number": phone_number,
                "message": message,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        logger.exception("WhatsApp send failed for %s", phone_number)
        raise AccountServiceError(
            "Unable to send verification code. Please try again.",
            code="whatsapp_send_failed",
        ) from exc

    if response.status_code >= 400:
        logger.warning(
            "WhatsApp API error status=%s body=%s",
            response.status_code,
            response.text[:300],
        )
        raise AccountServiceError(
            "Unable to send verification code. Please try again.",
            code="whatsapp_send_failed",
        )
