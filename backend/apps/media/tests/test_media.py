"""Tests for media upload validation."""

import io
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.media.models import PostMedia

User = get_user_model()
POSTS_URL = "/api/v1/posts/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="media@example.com",
        username="mediauser",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def _png(name="ok.png", size=(64, 64)) -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", size, color=(10, 120, 80)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_image_upload_works(api_client, user):
    _auth(api_client, user)
    response = api_client.post(
        POSTS_URL,
        {"content": "img", "media": _png()},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["media"][0]["media_type"] == "IMAGE"
    assert PostMedia.objects.count() == 1


def test_invalid_file_rejected(api_client, user):
    _auth(api_client, user)
    evil = SimpleUploadedFile(
        "malware.exe",
        b"MZ\x90\x00fake",
        content_type="application/octet-stream",
    )
    response = api_client.post(
        POSTS_URL,
        {"content": "nope", "media": evil},
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_large_image_rejected(api_client, user, monkeypatch):
    monkeypatch.setattr("apps.media.validators.MAX_IMAGE_SIZE_BYTES", 100)
    _auth(api_client, user)
    big = SimpleUploadedFile(
        "huge.png",
        b"x" * 120,
        content_type="image/png",
    )
    response = api_client.post(
        POSTS_URL,
        {"content": "big", "media": big},
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_large_video_rejected(api_client, user, monkeypatch):
    monkeypatch.setattr("apps.media.validators.MAX_VIDEO_SIZE_BYTES", 100)
    _auth(api_client, user)
    big = SimpleUploadedFile(
        "huge.mp4",
        b"x" * 120,
        content_type="video/mp4",
    )
    response = api_client.post(
        POSTS_URL,
        {"content": "bigvid", "media": big},
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.media.tasks.process_video_task.delay")
def test_video_upload_works(
    mock_delay, api_client, user, django_capture_on_commit_callbacks
):
    _auth(api_client, user)
    video = SimpleUploadedFile(
        "clip.mp4",
        b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64,
        content_type="video/mp4",
    )
    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            POSTS_URL,
            {"content": "vid", "media": video},
            format="multipart",
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["media"][0]["media_type"] == "VIDEO"
    assert response.data["media"][0]["processing_status"] == "PENDING"
    mock_delay.assert_called_once()
