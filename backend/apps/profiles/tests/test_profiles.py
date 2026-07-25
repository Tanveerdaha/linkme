"""Tests for profile expansion, privacy, completion, search, and activity."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.posts.models import Post
from apps.profiles.completion import calculate_profile_completion
from apps.profiles.models import Profile, ProfileSection
from apps.reactions.models import Reaction

User = get_user_model()

ME_URL = "/api/v1/profile/me/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def verified_user(db):
    return User.objects.create_user(
        email="jane@example.com",
        username="janedoe",
        password="SecurePass123!",
        first_name="Jane",
        last_name="Doe",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com",
        username="otheruser",
        password="SecurePass123!",
        first_name="Other",
        last_name="User",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def auth_client(api_client, verified_user):
    refresh = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


def test_profile_created_automatically(verified_user):
    assert Profile.objects.filter(user=verified_user).exists()


def test_get_me_profile(auth_client, verified_user):
    response = auth_client.get(ME_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == verified_user.username
    assert response.data["email"] == verified_user.email
    assert "completion" in response.data
    assert "statistics" in response.data
    assert "profile_visibility" in response.data
    assert "password" not in response.data


def test_update_own_profile(auth_client, verified_user):
    response = auth_client.patch(
        ME_URL,
        {
            "bio": "Building products",
            "headline": "Software Engineer",
            "location": "Pakistan",
            "first_name": "Janet",
            "profile_visibility": "PRIVATE",
            "pronouns": "she/her",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["bio"] == "Building products"
    assert response.data["profile_visibility"] == "PRIVATE"
    assert response.data["pronouns"] == "she/her"
    assert response.data["completion"]["percentage"] >= 35


def test_cannot_update_another_profile_via_me(auth_client, other_user):
    response = auth_client.patch(ME_URL, {"bio": "hijacked"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    other_user.profile.refresh_from_db()
    assert other_user.profile.bio == ""


def test_public_profile_visibility(api_client, verified_user):
    verified_user.profile.bio = "Hello world"
    verified_user.profile.headline = "Engineer"
    verified_user.profile.save()

    response = api_client.get(f"/api/v1/profile/{verified_user.username}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == verified_user.username
    assert response.data["name"] == "Jane Doe"
    assert response.data["bio"] == "Hello world"
    assert "email" not in response.data
    assert "joined_date" in response.data
    assert "statistics" in response.data


def test_private_profile_limited_for_guests(api_client, verified_user):
    profile = verified_user.profile
    profile.bio = "Secret bio"
    profile.headline = "Hidden headline"
    profile.profile_visibility = Profile.Visibility.PRIVATE
    profile.save()

    response = api_client.get(f"/api/v1/profile/{verified_user.username}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == "janedoe"
    assert response.data["is_private"] is True
    assert response.data["bio"] == ""
    assert response.data["headline"] == ""


def test_private_profile_full_for_owner(auth_client, verified_user):
    profile = verified_user.profile
    profile.bio = "Secret bio"
    profile.profile_visibility = Profile.Visibility.PRIVATE
    profile.save()

    response = auth_client.get(f"/api/v1/profile/{verified_user.username}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_private"] is False
    assert response.data["bio"] == "Secret bio"


def test_public_profile_hides_unverified(api_client, db):
    User.objects.create_user(
        email="hidden@example.com",
        username="hiddenuser",
        password="SecurePass123!",
        is_active=False,
        is_verified=False,
    )
    response = api_client.get("/api/v1/profile/hiddenuser/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_me_requires_auth(api_client):
    response = api_client.get(ME_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_profile_completion_calculation(verified_user):
    profile = verified_user.profile
    result = calculate_profile_completion(profile)
    assert result["percentage"] == 0
    assert "avatar" in result["missing"]

    profile.headline = "Engineer"
    profile.bio = "Hello"
    profile.location = "London"
    profile.save()
    result = calculate_profile_completion(profile)
    assert result["percentage"] == 45
    assert "avatar" in result["missing"]


def test_profile_sections_created(verified_user):
    from apps.profiles.services import ensure_default_sections

    ensure_default_sections(verified_user.profile)
    types = set(
        ProfileSection.objects.filter(profile=verified_user.profile).values_list(
            "section_type", flat=True
        )
    )
    assert ProfileSection.SectionType.ABOUT in types
    assert ProfileSection.SectionType.MEDIA in types


def test_search_username(api_client, verified_user):
    verified_user.profile.headline = "Product designer"
    verified_user.profile.save()
    response = api_client.get("/api/v1/search/users/", {"q": "jane"})
    assert response.status_code == status.HTTP_200_OK
    usernames = [r["username"] for r in response.data["results"]]
    assert "janedoe" in usernames


def test_search_headline(api_client, verified_user):
    verified_user.profile.headline = "Backend developer in London"
    verified_user.profile.save()
    response = api_client.get("/api/v1/search/users/", {"q": "Backend"})
    assert response.status_code == status.HTTP_200_OK
    assert any(r["username"] == "janedoe" for r in response.data["results"])


def test_search_location_filter(api_client, verified_user, other_user):
    verified_user.profile.location = "London"
    verified_user.profile.headline = "Dev"
    verified_user.profile.save()
    other_user.profile.location = "Paris"
    other_user.profile.headline = "Dev"
    other_user.profile.save()

    response = api_client.get(
        "/api/v1/search/users/", {"q": "Dev", "location": "London"}
    )
    assert response.status_code == status.HTTP_200_OK
    usernames = [r["username"] for r in response.data["results"]]
    assert "janedoe" in usernames
    assert "otheruser" not in usernames


def test_empty_search_returns_public_profiles(api_client, verified_user):
    response = api_client.get("/api/v1/search/users/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert "count" in response.data


def test_search_pagination(api_client, db):
    for i in range(25):
        user = User.objects.create_user(
            email=f"u{i}@example.com",
            username=f"user{i:02d}",
            password="SecurePass123!",
            is_active=True,
            is_verified=True,
        )
        user.profile.headline = f"Person {i}"
        user.profile.save()

    response = api_client.get("/api/v1/search/users/", {"page_size": 10})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 10
    assert response.data["next"] is not None


def test_activity_includes_post_comment_reaction(api_client, verified_user):
    post = Post.objects.create(
        author=verified_user,
        content="My first post",
        visibility=Post.Visibility.PUBLIC,
        status=Post.Status.PUBLISHED,
    )
    Comment.objects.create(author=verified_user, post=post, content="Self comment")
    Reaction.objects.create(
        user=verified_user, post=post, reaction_type=Reaction.ReactionType.HEART
    )

    response = api_client.get(f"/api/v1/profile/{verified_user.username}/activity/")
    assert response.status_code == status.HTTP_200_OK
    types = {item["type"] for item in response.data}
    assert "POST_CREATED" in types
    assert "COMMENT_CREATED" in types
    assert "REACTION_CREATED" in types


def test_media_gallery_empty(api_client, verified_user):
    response = api_client.get(f"/api/v1/profile/{verified_user.username}/media/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["images"] == []
    assert response.data["videos"] == []


def test_suggestions_endpoint(api_client, verified_user):
    verified_user.profile.headline = "Creator"
    verified_user.profile.save()
    response = api_client.get("/api/v1/users/suggestions/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
