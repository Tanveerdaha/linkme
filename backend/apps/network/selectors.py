"""Read selectors for connections and mutual network."""

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from apps.network.models import Connection
from apps.profiles.models import Profile

User = get_user_model()


def connection_partner(connection: Connection, viewer) -> User:
    """Return the other user on a connection relative to viewer."""
    if connection.sender_id == viewer.id:
        return connection.receiver
    return connection.sender


def get_accepted_connections(*, user) -> QuerySet:
    """Return ACCEPTED Connection rows involving ``user``."""
    return (
        Connection.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status=Connection.Status.ACCEPTED,
        )
        .select_related(
            "sender",
            "receiver",
            "sender__profile",
            "receiver__profile",
        )
        .order_by("-accepted_at", "-updated_at")
    )


def get_connected_user_ids(user) -> set:
    qs = Connection.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status=Connection.Status.ACCEPTED,
    ).values_list("sender_id", "receiver_id")
    ids: set = set()
    for sender_id, receiver_id in qs:
        ids.add(sender_id if sender_id != user.id else receiver_id)
    return ids


def get_received_requests(*, user) -> QuerySet:
    return (
        Connection.objects.filter(
            receiver=user,
            status=Connection.Status.PENDING,
        )
        .select_related("sender", "sender__profile")
        .order_by("-created_at")
    )


def get_sent_requests(*, user) -> QuerySet:
    return (
        Connection.objects.filter(
            sender=user,
            status=Connection.Status.PENDING,
        )
        .select_related("receiver", "receiver__profile")
        .order_by("-created_at")
    )


def get_mutual_connections(*, user1, user2, limit: int = 50) -> list:
    """Return profiles of users connected to both user1 and user2."""
    ids1 = get_connected_user_ids(user1)
    ids2 = get_connected_user_ids(user2)
    mutual_ids = ids1 & ids2
    mutual_ids.discard(user1.id)
    mutual_ids.discard(user2.id)

    if not mutual_ids:
        return []

    return list(
        Profile.objects.select_related("user")
        .filter(
            user_id__in=mutual_ids,
            user__is_active=True,
            user__is_verified=True,
        )
        .order_by("user__username")[:limit]
    )


def filter_connections_by_search(connections: QuerySet, search: str) -> QuerySet:
    term = (search or "").strip()
    if not term:
        return connections
    return connections.filter(
        Q(sender__username__icontains=term)
        | Q(sender__first_name__icontains=term)
        | Q(sender__last_name__icontains=term)
        | Q(sender__profile__headline__icontains=term)
        | Q(receiver__username__icontains=term)
        | Q(receiver__first_name__icontains=term)
        | Q(receiver__last_name__icontains=term)
        | Q(receiver__profile__headline__icontains=term)
    )


def can_view_connections_list(*, owner_profile: Profile, viewer) -> bool:
    """Respect connection_visibility on the owner's profile."""
    visibility = owner_profile.connection_visibility
    is_owner = bool(
        viewer
        and getattr(viewer, "is_authenticated", False)
        and viewer.id == owner_profile.user_id
    )
    if is_owner:
        return True
    if visibility == Profile.ConnectionVisibility.PUBLIC:
        return True
    if visibility == Profile.ConnectionVisibility.PRIVATE:
        return False
    if visibility == Profile.ConnectionVisibility.CONNECTIONS_ONLY:
        from apps.network.services import are_connected

        return bool(
            viewer
            and getattr(viewer, "is_authenticated", False)
            and are_connected(viewer, owner_profile.user)
        )
    return False
