"""Domain services for profile reads and updates."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.accounts.bloom import get_username_bloom
from apps.accounts.username_service import assert_username_available
from apps.profiles.completion import calculate_profile_completion
from apps.profiles.models import Profile, ProfileSection
from apps.profiles.statistics import get_profile_statistics

User = get_user_model()

DEFAULT_SECTIONS = [
    (ProfileSection.SectionType.ABOUT, 0),
    (ProfileSection.SectionType.INTERESTS, 1),
    (ProfileSection.SectionType.ACTIVITY, 2),
    (ProfileSection.SectionType.MEDIA, 3),
]


def get_profile_for_user(user) -> Profile:
    profile, created = Profile.objects.select_related("user").get_or_create(user=user)
    if created:
        ensure_default_sections(profile)
    return profile


def ensure_default_sections(profile: Profile) -> None:
    """Create MVP profile section shells if missing."""
    existing = set(profile.sections.values_list("section_type", flat=True))
    to_create = [
        ProfileSection(
            profile=profile,
            section_type=section_type,
            order=order,
            content={},
        )
        for section_type, order in DEFAULT_SECTIONS
        if section_type not in existing
    ]
    if to_create:
        ProfileSection.objects.bulk_create(to_create)


def get_public_profile(username: str, viewer=None) -> Profile:
    from rest_framework.exceptions import NotFound

    from apps.moderation.blocks import is_blocked

    user = get_object_or_404(
        User.objects.select_related("profile"),
        username__iexact=username,
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    profile = get_profile_for_user(user)
    ensure_default_sections(profile)

    is_owner = bool(
        viewer and getattr(viewer, "is_authenticated", False) and viewer.id == user.id
    )

    if (
        viewer
        and getattr(viewer, "is_authenticated", False)
        and not is_owner
        and is_blocked(user_a=viewer, user_b=user)
    ):
        raise NotFound("Profile not found.")

    if profile.profile_visibility == Profile.Visibility.PRIVATE and not is_owner:
        # Limited view: still return the profile object; serializer strips fields.
        profile._limited_view = True  # type: ignore[attr-defined]
    else:
        profile._limited_view = False  # type: ignore[attr-defined]
    return profile


def can_view_full_profile(profile: Profile, viewer) -> bool:
    if profile.profile_visibility == Profile.Visibility.PUBLIC:
        return True
    return bool(
        viewer
        and getattr(viewer, "is_authenticated", False)
        and viewer.id == profile.user_id
    )


@transaction.atomic
def update_own_profile(user, *, data: dict, files: dict | None = None) -> Profile:
    """Update the authenticated user's profile and related name fields."""
    profile = get_profile_for_user(user)
    files = files or {}
    old_username = user.username
    new_username = None

    user_fields = []
    if "username" in data:
        candidate = data["username"]
        if candidate != user.username:
            try:
                new_username = assert_username_available(
                    candidate, exclude_user_id=user.pk
                )
            except Exception as exc:
                # Map account service errors to API validation errors.
                from apps.accounts.services import AccountServiceError

                if isinstance(exc, AccountServiceError):
                    raise ValidationError({"username": [exc.message]}) from exc
                raise
            user.username = new_username
            user_fields.append("username")

    for field in ("first_name", "last_name"):
        if field in data:
            setattr(user, field, data[field])
            user_fields.append(field)
    if user_fields:
        user_fields.append("updated_at")
        try:
            user.save(update_fields=user_fields)
        except IntegrityError as exc:
            raise ValidationError({"username": ["Username already exists"]}) from exc
        if new_username:
            get_username_bloom().add_username(new_username)

    profile_fields = []
    text_fields = (
        "bio",
        "headline",
        "location",
        "website",
        "interests",
        "pronouns",
        "birth_date",
        "social_links",
        "profile_visibility",
        "connection_visibility",
    )
    for field in text_fields:
        if field in data:
            setattr(profile, field, data[field])
            profile_fields.append(field)

    if "avatar" in files:
        profile.avatar = files["avatar"]
        profile_fields.append("avatar")
    if "cover_image" in files:
        profile.cover_image = files["cover_image"]
        profile_fields.append("cover_image")

    if profile_fields:
        profile_fields.append("updated_at")
        profile.save(update_fields=profile_fields)
        from apps.moderation.audit import log_audit
        from apps.moderation.models import AuditLog

        log_audit(
            user=user,
            action=AuditLog.Action.PROFILE_UPDATE,
            object_type="profile",
            object_id=str(profile.id) if hasattr(profile, "id") else str(user.id),
        )
    else:
        profile.save()

    # Keep PrivacySetting in sync when visibility fields change.
    if "profile_visibility" in data or "connection_visibility" in data:
        from apps.privacy.services import get_or_create_privacy_settings

        privacy = get_or_create_privacy_settings(user)
        sync_fields = []
        if "profile_visibility" in data:
            privacy.profile_visibility = data["profile_visibility"]
            sync_fields.append("profile_visibility")
        if "connection_visibility" in data:
            privacy.connection_visibility = data["connection_visibility"]
            sync_fields.append("connection_visibility")
        if sync_fields:
            sync_fields.append("updated_at")
            privacy.save(update_fields=sync_fields)

    ensure_default_sections(profile)
    from apps.common.cache import invalidate_user_profile

    invalidate_user_profile(old_username)
    if new_username and new_username != old_username:
        invalidate_user_profile(new_username)
    return profile


def build_me_profile_payload(profile: Profile, request) -> dict:
    from apps.profiles.serializers import MeProfileSerializer

    data = MeProfileSerializer(profile, context={"request": request}).data
    data["completion"] = calculate_profile_completion(profile)
    data["statistics"] = get_profile_statistics(profile)
    return data


def build_public_profile_payload(profile: Profile, request) -> dict:
    from apps.common.cache import cache_user_profile
    from apps.profiles.serializers import PublicProfileSerializer

    limited = getattr(profile, "_limited_view", False)
    viewer = getattr(request, "user", None)
    is_authenticated_viewer = bool(
        viewer and getattr(viewer, "is_authenticated", False)
    )
    # Only cache anonymous / owner-neutral public views.
    cacheable = not limited and not is_authenticated_viewer
    if cacheable:
        cached = cache_user_profile(profile.user.username)
        if cached is not None:
            return cached

    data = PublicProfileSerializer(
        profile, context={"request": request, "limited": limited}
    ).data
    if not limited:
        data["statistics"] = get_profile_statistics(profile)
    else:
        data["statistics"] = {"posts": 0, "media": 0, "profile_views": 0}
        # Strip rich fields for private profiles.
        for key in (
            "bio",
            "headline",
            "location",
            "website",
            "interests",
            "pronouns",
            "social_links",
            "cover_image",
            "birth_date",
        ):
            if key in data:
                if key in ("interests",):
                    data[key] = []
                elif key == "social_links":
                    data[key] = {}
                else:
                    data[key] = None if key in ("cover_image", "birth_date") else ""
    data["is_private"] = limited
    if cacheable:
        cache_user_profile(profile.user.username, data)
    return data
