"""Phase 9 admin dashboard tests."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.admin_dashboard.models import AdminPermissionCode, AdminRole
from apps.admin_dashboard.services import ensure_admin_role
from apps.moderation.models import AuditLog, Report
from apps.posts.models import Post

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def _make_user(username: str, *, staff: bool = False, role: str | None = None) -> User:
    user = User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
        is_staff=staff or role is not None,
    )
    if role:
        ensure_admin_role(user=user, role=role)
    return user


def _auth(client: APIClient, user: User) -> APIClient:
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def normal_user(db):
    return _make_user("member")


@pytest.fixture
def moderator(db):
    return _make_user("mod", role=AdminRole.Role.MODERATOR)


@pytest.fixture
def analyst(db):
    return _make_user("analyst", role=AdminRole.Role.ANALYST)


@pytest.fixture
def super_admin(db):
    user = _make_user("root", staff=True, role=AdminRole.Role.SUPER_ADMIN)
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    return user


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_normal_user_denied(api_client, normal_user):
    _auth(api_client, normal_user)
    assert api_client.get("/api/v1/admin/analytics/overview/").status_code == 403
    assert api_client.get("/api/v1/admin/users/").status_code == 403


def test_admin_allowed(api_client, moderator):
    _auth(api_client, moderator)
    response = api_client.get("/api/v1/admin/analytics/overview/")
    assert response.status_code == 200
    assert "users" in response.data
    assert "reports" in response.data


def test_permission_restrictions_work(api_client, analyst):
    _auth(api_client, analyst)
    # Analyst can view analytics and users
    assert api_client.get("/api/v1/admin/analytics/overview/").status_code == 200
    assert api_client.get("/api/v1/admin/users/").status_code == 200
    # Analyst cannot suspend
    target = _make_user("victim")
    resp = api_client.post(
        f"/api/v1/admin/users/{target.id}/suspend/",
        {"reason": "test", "duration": "7_days"},
        format="json",
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def test_view_users(api_client, moderator, normal_user):
    _auth(api_client, moderator)
    response = api_client.get("/api/v1/admin/users/")
    assert response.status_code == 200
    assert "results" in response.data
    usernames = [u["username"] for u in response.data["results"]]
    assert normal_user.username in usernames


def test_suspend_user(api_client, moderator, normal_user):
    _auth(api_client, moderator)
    response = api_client.post(
        f"/api/v1/admin/users/{normal_user.id}/suspend/",
        {"reason": "Spam activity", "duration": "7_days"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["suspended"] is True
    normal_user.refresh_from_db()
    assert normal_user.is_suspended is True
    assert AuditLog.objects.filter(
        action=AuditLog.Action.MODERATION_ACTION,
        object_id=str(normal_user.id),
    ).exists()


def test_restore_user(api_client, moderator, normal_user):
    normal_user.is_suspended = True
    normal_user.suspension_reason = "x"
    normal_user.save()
    _auth(api_client, moderator)
    response = api_client.post(f"/api/v1/admin/users/{normal_user.id}/unsuspend/")
    assert response.status_code == 200
    normal_user.refresh_from_db()
    assert normal_user.is_suspended is False


def test_user_detail(api_client, moderator, normal_user):
    _auth(api_client, moderator)
    response = api_client.get(f"/api/v1/admin/users/{normal_user.id}/")
    assert response.status_code == 200
    assert response.data["username"] == normal_user.username
    assert "posts_count" in response.data


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def test_view_and_resolve_report(api_client, moderator, normal_user):
    author = _make_user("author1")
    post = Post.objects.create(
        author=author,
        content="spam",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    report = Report.objects.create(
        reporter=normal_user,
        reported_user=author,
        content_type_label=Report.ContentTypeChoice.POST,
        object_id=str(post.id),
        reason=Report.Reason.SPAM,
        status=Report.Status.PENDING,
    )

    _auth(api_client, moderator)
    listing = api_client.get("/api/v1/admin/reports/")
    assert listing.status_code == 200
    assert any(r["id"] == str(report.id) for r in listing.data["results"])

    resolved = api_client.patch(
        f"/api/v1/admin/reports/{report.id}/",
        {"status": "RESOLVE", "note": "Confirmed spam"},
        format="json",
    )
    assert resolved.status_code == 200
    assert resolved.data["status"] == Report.Status.RESOLVED
    assert AuditLog.objects.filter(
        object_type="report", object_id=str(report.id)
    ).exists()


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


def test_remove_post(api_client, moderator):
    author = _make_user("poster")
    post = Post.objects.create(
        author=author,
        content="bad",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    _auth(api_client, moderator)
    response = api_client.delete(
        f"/api/v1/admin/content/posts/{post.id}/",
        {"reason": "Policy"},
        format="json",
    )
    assert response.status_code == 200
    post.refresh_from_db()
    assert post.status == Post.Status.DELETED


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_admin_action_creates_audit(api_client, moderator, normal_user):
    _auth(api_client, moderator)
    api_client.post(
        f"/api/v1/admin/users/{normal_user.id}/suspend/",
        {"reason": "Abuse", "duration": "3_days"},
        format="json",
    )
    logs = api_client.get("/api/v1/admin/audit/")
    assert logs.status_code == 200
    assert len(logs.data["results"]) >= 1


def test_admin_me(api_client, moderator):
    _auth(api_client, moderator)
    response = api_client.get("/api/v1/admin/me/")
    assert response.status_code == 200
    assert response.data["role"] == "MODERATOR"
    assert AdminPermissionCode.VIEW_REPORTS in response.data["permissions"]


def test_export_request(api_client, analyst):
    _auth(api_client, analyst)
    response = api_client.post(
        "/api/v1/admin/export/",
        {"export_type": "USERS", "format": "CSV"},
        format="json",
    )
    assert response.status_code == 202
    assert response.data["status"] in ("PENDING", "PROCESSING", "READY")
