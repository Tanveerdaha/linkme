"""Tests for post and comment reactions."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.posts.models import Post
from apps.reactions.models import Reaction

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="alice@example.com",
        username="alice",
        password="SecurePass123!",
        first_name="Alice",
        last_name="A",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="bob@example.com",
        username="bob",
        password="SecurePass123!",
        first_name="Bob",
        last_name="B",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def public_post(user_a):
    return Post.objects.create(
        author=user_a,
        content="Engage with me",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_authenticated_user_reacts(api_client, user_a, public_post):
    _auth(api_client, user_a)
    response = api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["reacted"] is True
    assert response.data["reaction_type"] == "HEART"
    assert response.data["count"] == 1
    assert Reaction.objects.filter(user=user_a, post=public_post).count() == 1


def test_guest_cannot_react(api_client, public_post):
    response = api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_duplicate_reaction_prevented(api_client, user_a, public_post):
    _auth(api_client, user_a)
    first = api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    second = api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_200_OK
    assert second.data["count"] == 1
    assert Reaction.objects.filter(user=user_a, post=public_post).count() == 1


def test_remove_reaction(api_client, user_a, public_post):
    _auth(api_client, user_a)
    api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    response = api_client.delete(f"/api/v1/posts/{public_post.id}/reaction/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["reacted"] is False
    assert response.data["count"] == 0
    assert not Reaction.objects.filter(user=user_a, post=public_post).exists()


def test_reaction_count_correct(api_client, user_a, user_b, public_post):
    _auth(api_client, user_a)
    api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")
    _auth(api_client, user_b)
    api_client.post(f"/api/v1/posts/{public_post.id}/reaction/")

    summary = api_client.get(f"/api/v1/posts/{public_post.id}/reactions/")
    assert summary.status_code == status.HTTP_200_OK
    assert summary.data["total"] == 2
    assert summary.data["heart"] == 2


def test_comment_reaction(api_client, user_a, user_b, public_post):
    comment = Comment.objects.create(
        author=user_a,
        post=public_post,
        content="Nice!",
    )
    _auth(api_client, user_b)
    response = api_client.post(f"/api/v1/comments/{comment.id}/reaction/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["reacted"] is True
    assert response.data["count"] == 1

    removed = api_client.delete(f"/api/v1/comments/{comment.id}/reaction/")
    assert removed.data["reacted"] is False
    assert removed.data["count"] == 0
