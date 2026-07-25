"""Block relationship helpers used across apps."""

from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.moderation.models import BlockedUser

User = get_user_model()


def is_blocked(*, user_a, user_b) -> bool:
    """True when either user has blocked the other."""
    if not user_a or not user_b:
        return False
    if getattr(user_a, "id", None) is None or getattr(user_b, "id", None) is None:
        return False
    if user_a.id == user_b.id:
        return False
    return BlockedUser.objects.filter(
        Q(blocker=user_a, blocked_user=user_b)
        | Q(blocker=user_b, blocked_user=user_a)
    ).exists()


def has_blocked(*, blocker, blocked) -> bool:
    """True when ``blocker`` specifically blocked ``blocked``."""
    if not blocker or not blocked:
        return False
    return BlockedUser.objects.filter(blocker=blocker, blocked_user=blocked).exists()


def blocked_user_ids_for(user) -> set:
    """Return IDs of users blocked by or blocking ``user``."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    rows = BlockedUser.objects.filter(
        Q(blocker=user) | Q(blocked_user=user)
    ).values_list("blocker_id", "blocked_user_id")
    ids: set = set()
    for blocker_id, blocked_id in rows:
        if blocker_id != user.id:
            ids.add(blocker_id)
        if blocked_id != user.id:
            ids.add(blocked_id)
    return ids


def assert_not_blocked(*, actor, target) -> None:
    """Raise PermissionDenied when a block exists between actor and target."""
    from rest_framework.exceptions import PermissionDenied

    if is_blocked(user_a=actor, user_b=target):
        raise PermissionDenied("You cannot interact with this user.")


def assert_user_can_act(user) -> None:
    """Raise PermissionDenied when the user is suspended or soft-deleted."""
    from rest_framework.exceptions import PermissionDenied

    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Authentication required.")
    if getattr(user, "is_deleted", False):
        raise PermissionDenied("This account has been deleted.")
    if hasattr(user, "is_currently_suspended") and user.is_currently_suspended():
        raise PermissionDenied("This account is suspended.")
