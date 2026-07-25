"""Tests for engagement counters on posts and share links."""

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
        content="Counted post",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_post_returns_reaction_and_comment_counts(
    api_client, user_a, user_b, public_post
):
    Reaction.objects.create(
        user=user_a, post=public_post, reaction_type=Reaction.ReactionType.HEART
    )
    Reaction.objects.create(
        user=user_b, post=public_post, reaction_type=Reaction.ReactionType.HEART
    )
    Comment.objects.create(author=user_b, post=public_post, content="One")
    Comment.objects.create(author=user_a, post=public_post, content="Two")
    deleted = Comment.objects.create(
        author=user_a, post=public_post, content="Gone"
    )
    deleted.status = Comment.Status.DELETED
    deleted.save(update_fields=["status", "updated_at"])

    response = api_client.get(f"/api/v1/posts/{public_post.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["reaction_count"] == 2
    assert response.data["comment_count"] == 2
    assert response.data["user_reacted"] is False


def test_user_reaction_status_correct(api_client, user_a, public_post):
    Reaction.objects.create(
        user=user_a, post=public_post, reaction_type=Reaction.ReactionType.HEART
    )
    _auth(api_client, user_a)
    response = api_client.get(f"/api/v1/posts/{public_post.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user_reacted"] is True


def test_feed_includes_engagement_fields(api_client, user_a, public_post):
    Reaction.objects.create(
        user=user_a, post=public_post, reaction_type=Reaction.ReactionType.HEART
    )
    Comment.objects.create(author=user_a, post=public_post, content="Hi")
    response = api_client.get("/api/v1/feed/public/")
    assert response.status_code == status.HTTP_200_OK
    post = response.data["results"][0]
    assert post["reaction_count"] == 1
    assert post["comment_count"] == 1
    assert "user_reacted" in post


def test_share_endpoint(api_client, public_post):
    response = api_client.get(f"/api/v1/posts/{public_post.id}/share/")
    assert response.status_code == status.HTTP_200_OK
    assert str(public_post.id) in response.data["url"]
    assert "/post/" in response.data["url"]
    assert "title" in response.data
