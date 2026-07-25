"""Online presence helpers backed by Redis."""

from django.core.cache import cache

PRESENCE_TTL_SECONDS = 60
PRESENCE_KEY_TEMPLATE = "user:{user_id}:online"
VIEWING_KEY_TEMPLATE = "user:{user_id}:viewing_conversation"


def _key(user_id) -> str:
    return PRESENCE_KEY_TEMPLATE.format(user_id=user_id)


def _viewing_key(user_id) -> str:
    return VIEWING_KEY_TEMPLATE.format(user_id=user_id)


def set_online(user_id, *, ttl: int = PRESENCE_TTL_SECONDS) -> None:
    """Mark user online with a sliding TTL (heartbeat renews)."""
    cache.set(_key(user_id), "1", timeout=ttl)


def set_offline(user_id) -> None:
    """Clear online presence for a user."""
    cache.delete(_key(user_id))
    clear_viewing_conversation(user_id)


def is_online(user_id) -> bool:
    """Return True when the user has an unexpired online key."""
    return bool(cache.get(_key(user_id)))


def heartbeat(user_id, *, ttl: int = PRESENCE_TTL_SECONDS) -> None:
    """Refresh presence TTL — called from WebSocket heartbeat events."""
    set_online(user_id, ttl=ttl)
    viewing = get_viewing_conversation(user_id)
    if viewing:
        set_viewing_conversation(user_id, viewing, ttl=ttl)


def get_online_map(user_ids) -> dict:
    """Return ``{user_id: bool}`` for the given ids."""
    return {uid: is_online(uid) for uid in user_ids}


def set_viewing_conversation(
    user_id, conversation_id, *, ttl: int = PRESENCE_TTL_SECONDS
) -> None:
    """Mark which conversation the user currently has open."""
    cache.set(_viewing_key(user_id), str(conversation_id), timeout=ttl)


def clear_viewing_conversation(user_id) -> None:
    cache.delete(_viewing_key(user_id))


def get_viewing_conversation(user_id) -> str | None:
    value = cache.get(_viewing_key(user_id))
    return str(value) if value else None
