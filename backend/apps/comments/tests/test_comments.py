"""Tests for comments and replies."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.posts.models import Post

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
        content="Discuss this",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_create_comment(api_client, user_b, public_post):
    _auth(api_client, user_b)
    response = api_client.post(
        f"/api/v1/posts/{public_post.id}/comments/",
        {"content": "Great post!"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "Great post!"
    assert response.data["author"]["username"] == "bob"
    assert Comment.objects.filter(post=public_post, parent=None).count() == 1


def test_guest_cannot_comment(api_client, public_post):
    response = api_client.post(
        f"/api/v1/posts/{public_post.id}/comments/",
        {"content": "Nope"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_edit_own_comment(api_client, user_b, public_post):
    comment = Comment.objects.create(
        author=user_b, post=public_post, content="Original"
    )
    _auth(api_client, user_b)
    response = api_client.patch(
        f"/api/v1/comments/{comment.id}/",
        {"content": "Edited"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["content"] == "Edited"


def test_cannot_edit_others_comment(api_client, user_a, user_b, public_post):
    comment = Comment.objects.create(
        author=user_a, post=public_post, content="Alice says"
    )
    _auth(api_client, user_b)
    response = api_client.patch(
        f"/api/v1/comments/{comment.id}/",
        {"content": "Hijack"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_comment_soft(api_client, user_b, public_post):
    comment = Comment.objects.create(
        author=user_b, post=public_post, content="Bye"
    )
    _auth(api_client, user_b)
    response = api_client.delete(f"/api/v1/comments/{comment.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    comment.refresh_from_db()
    assert comment.status == Comment.Status.DELETED


def test_reply_works(api_client, user_a, user_b, public_post):
    parent = Comment.objects.create(
        author=user_a, post=public_post, content="Top level"
    )
    _auth(api_client, user_b)
    response = api_client.post(
        f"/api/v1/comments/{parent.id}/reply/",
        {"content": "I agree!"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "I agree!"
    assert response.data["parent"] == str(parent.id)
    assert Comment.objects.filter(parent=parent).count() == 1


def test_reply_depth_restricted(api_client, user_a, user_b, public_post):
    parent = Comment.objects.create(
        author=user_a, post=public_post, content="Top"
    )
    reply = Comment.objects.create(
        author=user_b, post=public_post, parent=parent, content="Nested"
    )
    _auth(api_client, user_a)
    response = api_client.post(
        f"/api/v1/comments/{reply.id}/reply/",
        {"content": "Too deep"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_list_comments_includes_replies(api_client, user_a, user_b, public_post):
    parent = Comment.objects.create(
        author=user_a, post=public_post, content="Parent"
    )
    Comment.objects.create(
        author=user_b, post=public_post, parent=parent, content="Child"
    )
    response = api_client.get(f"/api/v1/posts/{public_post.id}/comments/")
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) == 1
    assert results[0]["content"] == "Parent"
    assert len(results[0]["replies"]) == 1
    assert results[0]["replies"][0]["content"] == "Child"


def test_create_reply_via_parent_comment_id(api_client, user_a, user_b, public_post):
    parent = Comment.objects.create(
        author=user_a, post=public_post, content="Top level"
    )
    _auth(api_client, user_b)
    response = api_client.post(
        f"/api/v1/posts/{public_post.id}/comments/",
        {
            "content": "Thanks via parent_comment_id",
            "parent_comment_id": str(parent.id),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["parent"] == str(parent.id)
    assert Comment.objects.filter(parent=parent).count() == 1


def test_parent_comment_id_must_match_post(api_client, user_a, user_b, public_post):
    other_post = Post.objects.create(
        author=user_a,
        content="Other",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
    )
    parent = Comment.objects.create(
        author=user_a, post=other_post, content="Wrong post"
    )
    _auth(api_client, user_b)
    response = api_client.post(
        f"/api/v1/posts/{public_post.id}/comments/",
        {
            "content": "Mismatch",
            "parent_comment_id": str(parent.id),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
