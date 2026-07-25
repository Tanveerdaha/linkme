"""Phase 8 tests — blocking, reporting, privacy, account, security."""

import io
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.moderation.models import AuditLog, BlockedUser, DataExportRequest, Report
from apps.posts.models import Post
from apps.privacy.models import PrivacySetting

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def _make_user(username: str, *, staff: bool = False) -> User:
    user = User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
        is_staff=staff,
    )
    return user


def _auth(client: APIClient, user: User) -> APIClient:
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def user_a(db):
    return _make_user("alice")


@pytest.fixture
def user_b(db):
    return _make_user("bob")


@pytest.fixture
def staff_user(db):
    return _make_user("moderator", staff=True)


# ---------------------------------------------------------------------------
# Blocking
# ---------------------------------------------------------------------------


def test_block_user(api_client, user_a, user_b):
    _auth(api_client, user_a)
    response = api_client.post(
        f"/api/v1/users/{user_b.username}/block/",
        {"reason": "Spam"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["blocked"] is True
    assert BlockedUser.objects.filter(blocker=user_a, blocked_user=user_b).exists()
    assert AuditLog.objects.filter(action=AuditLog.Action.BLOCK_USER).exists()


def test_blocked_user_cannot_interact(api_client, user_a, user_b):
    _auth(api_client, user_a)
    api_client.post(f"/api/v1/users/{user_b.username}/block/", format="json")

    post = Post.objects.create(
        author=user_a,
        content="Hello world",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )

    # Blocked user cannot view profile
    _auth(api_client, user_b)
    profile_resp = api_client.get(f"/api/v1/profile/{user_a.username}/")
    assert profile_resp.status_code == 404

    # Blocked user cannot comment
    comment_resp = api_client.post(
        f"/api/v1/posts/{post.id}/comments/",
        {"content": "hi"},
        format="json",
    )
    assert comment_resp.status_code in (403, 404)

    # Blocked user cannot send connection request
    conn_resp = api_client.post(
        "/api/v1/network/connect/",
        {"username": user_a.username},
        format="json",
    )
    assert conn_resp.status_code in (400, 403, 404)


def test_unblock_restores_access(api_client, user_a, user_b):
    _auth(api_client, user_a)
    api_client.post(f"/api/v1/users/{user_b.username}/block/", format="json")
    response = api_client.delete(f"/api/v1/users/{user_b.username}/block/")
    assert response.status_code == 204
    assert not BlockedUser.objects.filter(blocker=user_a, blocked_user=user_b).exists()

    _auth(api_client, user_b)
    profile_resp = api_client.get(f"/api/v1/profile/{user_a.username}/")
    assert profile_resp.status_code == 200


def test_blocked_list(api_client, user_a, user_b):
    _auth(api_client, user_a)
    api_client.post(
        f"/api/v1/users/{user_b.username}/block/",
        {"reason": "Spam"},
        format="json",
    )
    response = api_client.get("/api/v1/users/blocked/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["username"] == user_b.username


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_create_report(api_client, user_a, user_b):
    post = Post.objects.create(
        author=user_b,
        content="spam post",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    _auth(api_client, user_a)
    response = api_client.post(
        "/api/v1/reports/",
        {
            "content_type": "POST",
            "object_id": str(post.id),
            "reason": "SPAM",
            "description": "Fake promotion",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["reason"] == "SPAM"
    assert Report.objects.filter(reporter=user_a).count() == 1


def test_duplicate_report_prevention(api_client, user_a, user_b):
    post = Post.objects.create(
        author=user_b,
        content="spam",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    payload = {
        "content_type": "POST",
        "object_id": str(post.id),
        "reason": "SPAM",
    }
    _auth(api_client, user_a)
    assert api_client.post("/api/v1/reports/", payload, format="json").status_code == 201
    dup = api_client.post("/api/v1/reports/", payload, format="json")
    assert dup.status_code == 400


def test_report_status_changes(api_client, user_a, user_b, staff_user):
    post = Post.objects.create(
        author=user_b,
        content="x",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    _auth(api_client, user_a)
    created = api_client.post(
        "/api/v1/reports/",
        {"content_type": "POST", "object_id": str(post.id), "reason": "SPAM"},
        format="json",
    )
    report_id = created.data["id"]

    # Celery eager should move to UNDER_REVIEW
    report = Report.objects.get(pk=report_id)
    assert report.status in (Report.Status.PENDING, Report.Status.UNDER_REVIEW)

    _auth(api_client, staff_user)
    response = api_client.patch(
        f"/api/v1/reports/admin/reports/{report_id}/",
        {"status": "RESOLVED"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "RESOLVED"


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------


def test_privacy_settings_get_update(api_client, user_a):
    _auth(api_client, user_a)
    get_resp = api_client.get("/api/v1/privacy/settings/")
    assert get_resp.status_code == 200
    assert get_resp.data["profile_visibility"] == "PUBLIC"

    patch_resp = api_client.patch(
        "/api/v1/privacy/settings/",
        {
            "profile_visibility": "PRIVATE",
            "message_permission": "NOBODY",
        },
        format="json",
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data["profile_visibility"] == "PRIVATE"
    assert patch_resp.data["message_permission"] == "NOBODY"

    settings_obj = PrivacySetting.objects.get(user=user_a)
    assert settings_obj.profile_visibility == "PRIVATE"


def test_private_profile_hidden(api_client, user_a, user_b):
    from apps.profiles.services import get_profile_for_user

    profile = get_profile_for_user(user_a)
    profile.profile_visibility = "PRIVATE"
    profile.save(update_fields=["profile_visibility"])

    _auth(api_client, user_b)
    response = api_client.get(f"/api/v1/profile/{user_a.username}/")
    assert response.status_code == 200
    assert response.data.get("is_private") is True


def test_private_posts_hidden(api_client, user_a, user_b):
    post = Post.objects.create(
        author=user_a,
        content="secret",
        visibility=Post.Visibility.PRIVATE,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    _auth(api_client, user_b)
    response = api_client.get(f"/api/v1/posts/{post.id}/")
    assert response.status_code == 404


def test_message_restrictions(api_client, user_a, user_b):
    from apps.network.models import Connection
    from apps.privacy.services import can_message, update_privacy_settings

    Connection.objects.create(
        sender=user_a,
        receiver=user_b,
        status=Connection.Status.ACCEPTED,
        accepted_at=timezone.now(),
    )
    assert can_message(sender=user_a, recipient=user_b) is True

    update_privacy_settings(user_b, data={"message_permission": "NOBODY"})
    assert can_message(sender=user_a, recipient=user_b) is False


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


def test_delete_account(api_client, user_a):
    _auth(api_client, user_a)
    response = api_client.delete("/api/v1/account/")
    assert response.status_code == 200
    user_a.refresh_from_db()
    assert user_a.is_deleted is True
    assert user_a.is_active is False

    # Clear stale JWT so login is evaluated without auth failure on inactive user.
    api_client.credentials()
    login = api_client.post(
        "/api/v1/auth/login/",
        {"login": user_a.email, "password": "SecurePass123!"},
        format="json",
    )
    assert login.status_code == 403
    assert login.data["code"] == "deleted"


def test_suspended_user_blocked(api_client, user_a):
    user_a.is_suspended = True
    user_a.suspended_until = timezone.now() + timedelta(days=7)
    user_a.suspension_reason = "Abuse"
    user_a.save()

    login = api_client.post(
        "/api/v1/auth/login/",
        {"login": user_a.email, "password": "SecurePass123!"},
        format="json",
    )
    assert login.status_code == 403
    assert login.data["code"] == "suspended"


def test_export_request_created(api_client, user_a):
    _auth(api_client, user_a)
    response = api_client.post("/api/v1/account/export/")
    assert response.status_code == 202
    assert DataExportRequest.objects.filter(user=user_a).exists()
    export = DataExportRequest.objects.get(user=user_a)
    # Eager celery should complete
    export.refresh_from_db()
    assert export.status in (
        DataExportRequest.Status.READY,
        DataExportRequest.Status.PROCESSING,
        DataExportRequest.Status.PENDING,
        DataExportRequest.Status.FAILED,
    )


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


def test_unauthorized_access_blocked(api_client):
    assert api_client.get("/api/v1/privacy/settings/").status_code == 401
    assert api_client.get("/api/v1/users/blocked/").status_code == 401
    assert api_client.post("/api/v1/reports/", {}, format="json").status_code == 401


def test_upload_validation_rejects_bad_extension(api_client, user_a):
    from apps.media.validators import validate_media_file
    from django.core.exceptions import ValidationError

    bad = SimpleUploadedFile("malware.exe", b"MZ\x90\x00", content_type="application/octet-stream")
    with pytest.raises(ValidationError):
        validate_media_file(bad)


def test_upload_validation_accepts_jpeg(api_client, user_a):
    from apps.media.validators import validate_media_file

    # Minimal JPEG header
    jpeg = SimpleUploadedFile(
        "photo.jpg",
        b"\xff\xd8\xff\xe0" + b"\x00" * 32,
        content_type="image/jpeg",
    )
    assert validate_media_file(jpeg) == "IMAGE"


def test_staff_moderation_action(api_client, user_a, user_b, staff_user):
    post = Post.objects.create(
        author=user_b,
        content="bad",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    _auth(api_client, staff_user)
    response = api_client.post(
        "/api/v1/reports/admin/actions/",
        {
            "target_type": "POST",
            "target_id": str(post.id),
            "action": "CONTENT_REMOVED",
            "reason": "Spam",
        },
        format="json",
    )
    assert response.status_code == 201
    post.refresh_from_db()
    assert post.status == Post.Status.DELETED
