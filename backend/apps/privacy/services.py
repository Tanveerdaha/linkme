"""Privacy setting services."""

from django.db import transaction

from apps.moderation.audit import log_audit
from apps.moderation.models import AuditLog
from apps.privacy.models import PrivacySetting


def get_or_create_privacy_settings(user) -> PrivacySetting:
    """Return privacy settings, seeding from Profile when first created."""
    settings_obj, created = PrivacySetting.objects.get_or_create(user=user)
    if created:
        _sync_from_profile(settings_obj)
    return settings_obj


def _sync_from_profile(settings_obj: PrivacySetting) -> None:
    profile = getattr(settings_obj.user, "profile", None)
    if profile is None:
        return
    fields = []
    if profile.profile_visibility:
        settings_obj.profile_visibility = profile.profile_visibility
        fields.append("profile_visibility")
    if profile.connection_visibility:
        settings_obj.connection_visibility = profile.connection_visibility
        fields.append("connection_visibility")
    if fields:
        fields.append("updated_at")
        settings_obj.save(update_fields=fields)


@transaction.atomic
def update_privacy_settings(user, *, data: dict) -> PrivacySetting:
    settings_obj = get_or_create_privacy_settings(user)
    allowed = {
        "profile_visibility",
        "post_visibility",
        "connection_visibility",
        "message_permission",
    }
    changed = []
    for field in allowed:
        if field in data and data[field] is not None:
            setattr(settings_obj, field, data[field])
            changed.append(field)

    if changed:
        changed.append("updated_at")
        settings_obj.save(update_fields=changed)
        _sync_to_profile(settings_obj)
        log_audit(
            user=user,
            action=AuditLog.Action.PRIVACY_UPDATE,
            object_type="privacy",
            object_id=str(settings_obj.id),
            metadata={k: getattr(settings_obj, k) for k in allowed},
        )
    return settings_obj


def _sync_to_profile(settings_obj: PrivacySetting) -> None:
    """Keep Profile visibility fields in sync for existing consumers."""
    from apps.profiles.services import get_profile_for_user

    profile = get_profile_for_user(settings_obj.user)
    profile.profile_visibility = settings_obj.profile_visibility
    profile.connection_visibility = settings_obj.connection_visibility
    profile.save(
        update_fields=["profile_visibility", "connection_visibility", "updated_at"]
    )


def can_message(*, sender, recipient) -> bool:
    """Whether sender may message recipient based on privacy + blocks."""
    from apps.moderation.blocks import is_blocked
    from apps.network.services import are_connected

    if not sender or not recipient:
        return False
    if sender.id == recipient.id:
        return False
    if is_blocked(user_a=sender, user_b=recipient):
        return False
    if getattr(recipient, "is_deleted", False) or getattr(sender, "is_deleted", False):
        return False

    privacy = get_or_create_privacy_settings(recipient)
    if privacy.message_permission == PrivacySetting.MessagePermission.NOBODY:
        return False
    return are_connected(sender, recipient)


def can_view_post(*, post, viewer) -> bool:
    """Visibility + block + deletion checks for a post."""
    from apps.moderation.blocks import is_blocked
    from apps.network.services import are_connected
    from apps.posts.models import Post

    if post.status == Post.Status.DELETED:
        return False
    author = post.author
    if getattr(author, "is_deleted", False):
        return False

    is_owner = bool(
        viewer
        and getattr(viewer, "is_authenticated", False)
        and post.author_id == viewer.id
    )
    if is_owner:
        return True

    if viewer and getattr(viewer, "is_authenticated", False):
        if is_blocked(user_a=viewer, user_b=author):
            return False

    if post.status != Post.Status.PUBLISHED:
        return False

    if post.visibility == Post.Visibility.PUBLIC:
        return True

    if post.visibility == Post.Visibility.PRIVATE:
        return False

    if post.visibility == Post.Visibility.CONNECTIONS_ONLY:
        if not viewer or not getattr(viewer, "is_authenticated", False):
            return False
        return are_connected(viewer, author)

    return False
