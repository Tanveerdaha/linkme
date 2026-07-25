"""Tests for public and authenticated feeds."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.posts.models import Post

User = get_user_model()

PUBLIC_FEED_URL = "/api/v1/feed/public/"
USER_FEED_URL = "/api/v1/feed/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="feedalice@example.com",
        username="feedalice",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="feedbob@example.com",
        username="feedbob",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def seeded_posts(user_a, user_b):
    older = Post.objects.create(
        author=user_a,
        content="Older public",
        visibility=Post.Visibility.PUBLIC,
        published_at=timezone.now() - timedelta(hours=2),
    )
    newer = Post.objects.create(
        author=user_b,
        content="Newer public",
        visibility=Post.Visibility.PUBLIC,
        published_at=timezone.now() - timedelta(hours=1),
    )
    private = Post.objects.create(
        author=user_a,
        content="Private note",
        visibility=Post.Visibility.PRIVATE,
        published_at=timezone.now(),
    )
    deleted = Post.objects.create(
        author=user_b,
        content="Gone",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.DELETED,
        published_at=timezone.now(),
    )
    return {"older": older, "newer": newer, "private": private, "deleted": deleted}


def test_public_feed_accessible_without_login(api_client, seeded_posts):
    response = api_client.get(PUBLIC_FEED_URL)
    assert response.status_code == status.HTTP_200_OK
    contents = [item["content"] for item in response.data["results"]]
    assert "Newer public" in contents
    assert "Older public" in contents
    assert "Private note" not in contents
    assert "Gone" not in contents


def test_private_posts_hidden_from_public_feed(api_client, seeded_posts):
    response = api_client.get(PUBLIC_FEED_URL)
    ids = {item["id"] for item in response.data["results"]}
    assert str(seeded_posts["private"].id) not in ids


def test_newest_posts_first(api_client, seeded_posts):
    response = api_client.get(PUBLIC_FEED_URL)
    contents = [item["content"] for item in response.data["results"]]
    assert contents.index("Newer public") < contents.index("Older public")


def test_user_feed_includes_own_private(api_client, user_a, seeded_posts):
    _auth(api_client, user_a)
    response = api_client.get(USER_FEED_URL)
    assert response.status_code == status.HTTP_200_OK
    contents = [item["content"] for item in response.data["results"]]
    assert "Private note" in contents
    assert "Newer public" in contents
    assert "Gone" not in contents


def test_user_feed_requires_auth(api_client):
    response = api_client.get(USER_FEED_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pagination_works(api_client, user_a):
    for i in range(25):
        Post.objects.create(
            author=user_a,
            content=f"Post {i}",
            visibility=Post.Visibility.PUBLIC,
            published_at=timezone.now() - timedelta(minutes=i),
        )
    response = api_client.get(PUBLIC_FEED_URL)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None

    # Follow cursor
    next_url = response.data["next"]
    # next is absolute; strip to path+query for APIClient
    path = next_url.split("/api/v1", 1)[-1]
    path = "/api/v1" + path
    page2 = api_client.get(path)
    assert page2.status_code == status.HTTP_200_OK
    assert len(page2.data["results"]) == 5
