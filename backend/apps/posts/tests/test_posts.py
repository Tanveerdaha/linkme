"""Tests for post create / update / delete / visibility."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.posts.models import Post

User = get_user_model()

POSTS_URL = "/api/v1/posts/"


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


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def _tiny_png(name="photo.png") -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(20, 140, 90)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_create_post_authenticated(api_client, user_a):
    _auth(api_client, user_a)
    from apps.profiles.models import Profile

    profile, _ = Profile.objects.get_or_create(user=user_a)
    profile.headline = "UI/UX Designer"
    profile.save(update_fields=["headline"])

    response = api_client.post(
        POSTS_URL,
        {"content": "My first LinkMe post", "visibility": "PUBLIC"},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "My first LinkMe post"
    assert response.data["author"]["username"] == "alice"
    assert response.data["author"]["headline"] == "UI/UX Designer"
    assert Post.objects.filter(author=user_a).count() == 1


def test_guest_cannot_create_post(api_client):
    response = api_client.post(
        POSTS_URL,
        {"content": "Nope"},
        format="multipart",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_own_post(api_client, user_a):
    post = Post.objects.create(
        author=user_a,
        content="Original",
        visibility=Post.Visibility.PUBLIC,
    )
    _auth(api_client, user_a)
    response = api_client.patch(
        f"{POSTS_URL}{post.id}/",
        {"content": "Updated"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["content"] == "Updated"
    post.refresh_from_db()
    assert post.content == "Updated"


def test_cannot_update_another_users_post(api_client, user_a, user_b):
    post = Post.objects.create(
        author=user_a,
        content="Alice only",
        visibility=Post.Visibility.PUBLIC,
    )
    _auth(api_client, user_b)
    response = api_client.patch(
        f"{POSTS_URL}{post.id}/",
        {"content": "Hijack"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_own_post_soft(api_client, user_a):
    post = Post.objects.create(
        author=user_a,
        content="Bye",
        visibility=Post.Visibility.PUBLIC,
    )
    _auth(api_client, user_a)
    response = api_client.delete(f"{POSTS_URL}{post.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    post.refresh_from_db()
    assert post.status == Post.Status.DELETED
    # Soft-deleted post is hidden from retrieve
    response = api_client.get(f"{POSTS_URL}{post.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_private_post_visibility(api_client, user_a, user_b):
    post = Post.objects.create(
        author=user_a,
        content="Secret",
        visibility=Post.Visibility.PRIVATE,
    )
    # Guest cannot view
    response = api_client.get(f"{POSTS_URL}{post.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Other user cannot view
    _auth(api_client, user_b)
    response = api_client.get(f"{POSTS_URL}{post.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Owner can view
    _auth(api_client, user_a)
    response = api_client.get(f"{POSTS_URL}{post.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["content"] == "Secret"


def test_create_post_with_image(api_client, user_a):
    _auth(api_client, user_a)
    response = api_client.post(
        POSTS_URL,
        {
            "content": "With media",
            "visibility": "PUBLIC",
            "media": _tiny_png(),
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data["media"]) == 1
    assert response.data["media"][0]["media_type"] == "IMAGE"
