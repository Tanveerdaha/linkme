"""Notification preference helpers."""

from apps.notifications.models import Notification, NotificationPreference

TYPE_TO_PREFERENCE = {
    Notification.NotificationType.POST_REACTION: "post_reactions_enabled",
    Notification.NotificationType.POST_COMMENT: "comments_enabled",
    Notification.NotificationType.COMMENT_REPLY: "comments_enabled",
    Notification.NotificationType.COMMENT_REACTION: "comments_enabled",
    Notification.NotificationType.CONNECTION_REQUEST: "connection_enabled",
    Notification.NotificationType.CONNECTION_ACCEPTED: "connection_enabled",
    Notification.NotificationType.MESSAGE_RECEIVED: "messages_enabled",
}


def get_or_create_preferences(*, user) -> NotificationPreference:
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def is_type_enabled(*, user, notification_type: str) -> bool:
    """Return False when the user has disabled this notification category."""
    pref_field = TYPE_TO_PREFERENCE.get(notification_type)
    if pref_field is None:
        # ACCOUNT_EVENT and unknown types are always allowed.
        return True
    prefs = get_or_create_preferences(user=user)
    return bool(getattr(prefs, pref_field, True))


def update_preferences(*, user, **fields) -> NotificationPreference:
    prefs = get_or_create_preferences(user=user)
    allowed = {
        "post_reactions_enabled",
        "comments_enabled",
        "connection_enabled",
        "messages_enabled",
    }
    changed = []
    for key, value in fields.items():
        if key in allowed and value is not None:
            setattr(prefs, key, bool(value))
            changed.append(key)
    if changed:
        prefs.save(update_fields=[*changed, "updated_at"])
    return prefs
