"""Phone / WhatsApp OTP authentication tests."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.phone_otp import store_otp

User = get_user_model()

SEND_URL = "/api/v1/auth/phone/send/"
VERIFY_URL = "/api/v1/auth/phone/verify/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_phone_send_validates_number(api_client):
    response = api_client.post(SEND_URL, {"phone_number": "abc"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_phone_otp_flow_creates_user(api_client, settings):
    settings.WHATSAPP_API_URL = "https://example.test/messages/send"
    settings.WHATSAPP_API_KEY = "test-key"
    phone = "+923092670648"

    with (
        patch("apps.accounts.phone_otp.generate_otp_code", return_value="123456"),
        patch("apps.accounts.whatsapp.send_whatsapp_message") as send_mock,
    ):
        send_resp = api_client.post(SEND_URL, {"phone_number": phone}, format="json")

    assert send_resp.status_code == status.HTTP_200_OK, send_resp.data
    assert send_resp.data["phone_number"] == phone
    assert send_resp.data["resend_available_in"] == 120
    send_mock.assert_called_once()
    assert "123456" in send_mock.call_args.kwargs["message"]

    verify_resp = api_client.post(
        VERIFY_URL,
        {"phone_number": phone, "code": "123456"},
        format="json",
    )
    assert verify_resp.status_code == status.HTTP_200_OK, verify_resp.data
    assert "access" in verify_resp.data
    user = User.objects.get(phone_number=phone)
    assert user.auth_provider == User.AuthProvider.PHONE
    assert user.is_verified is True
    assert user.email is None


@pytest.mark.django_db
def test_phone_verify_invalid_code(api_client):
    phone = "+923001112222"
    store_otp(phone=phone, code="654321")
    response = api_client.post(
        VERIFY_URL,
        {"phone_number": phone, "code": "000000"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["code"] == "otp_invalid"


@pytest.mark.django_db
def test_phone_resend_cooldown(api_client, settings):
    settings.WHATSAPP_API_URL = "https://example.test/messages/send"
    settings.WHATSAPP_API_KEY = "test-key"
    phone = "+923009998887"

    with (
        patch("apps.accounts.phone_otp.generate_otp_code", return_value="111111"),
        patch("apps.accounts.whatsapp.send_whatsapp_message"),
    ):
        first = api_client.post(SEND_URL, {"phone_number": phone}, format="json")
        second = api_client.post(SEND_URL, {"phone_number": phone}, format="json")

    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert second.data["code"] == "otp_resend_cooldown"
