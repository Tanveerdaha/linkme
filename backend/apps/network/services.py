"""Domain services for connection requests and relationships."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.network.models import Connection

User = get_user_model()


def _get_active_user(username: str):
    return get_object_or_404(
        User.objects.select_related("profile"),
        username__iexact=username,
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )


def _active_relationship(user_a, user_b) -> Connection | None:
    return (
        Connection.objects.filter(
            Q(sender=user_a, receiver=user_b) | Q(sender=user_b, receiver=user_a),
            status__in=Connection.ACTIVE_STATUSES,
        )
        .select_related("sender", "receiver", "sender__profile", "receiver__profile")
        .first()
    )


def get_connection_status(*, viewer, username: str) -> dict:
    """
    Return relationship status relative to ``viewer``.

    Possible status values: NONE, REQUEST_SENT, REQUEST_RECEIVED, CONNECTED, BLOCKED.
    """
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return {"status": "NONE", "can_connect": False}

    if viewer.username.lower() == username.lower():
        return {"status": "NONE", "can_connect": False, "is_self": True}

    other = _get_active_user(username)
    rel = _active_relationship(viewer, other)

    if rel is None:
        return {"status": "NONE", "can_connect": True, "connection_id": None}

    if rel.status == Connection.Status.BLOCKED:
        return {"status": "BLOCKED", "can_connect": False, "connection_id": str(rel.id)}

    if rel.status == Connection.Status.ACCEPTED:
        return {
            "status": "CONNECTED",
            "can_connect": False,
            "connection_id": str(rel.id),
        }

    if rel.status == Connection.Status.PENDING:
        if rel.sender_id == viewer.id:
            return {
                "status": "REQUEST_SENT",
                "can_connect": False,
                "connection_id": str(rel.id),
            }
        return {
            "status": "REQUEST_RECEIVED",
            "can_connect": False,
            "connection_id": str(rel.id),
        }

    return {"status": "NONE", "can_connect": True, "connection_id": None}


@transaction.atomic
def send_connection_request(*, sender, username: str, message: str = "") -> Connection:
    from apps.moderation.blocks import assert_not_blocked, assert_user_can_act

    assert_user_can_act(sender)
    if sender.username.lower() == username.lower():
        raise ValidationError({"detail": "You cannot connect with yourself."})

    receiver = _get_active_user(username)
    assert_not_blocked(actor=sender, target=receiver)
    existing = _active_relationship(sender, receiver)
    if existing is not None:
        if existing.status == Connection.Status.ACCEPTED:
            raise ValidationError({"detail": "You are already connected."})
        if existing.status == Connection.Status.PENDING:
            raise ValidationError({"detail": "A connection request already exists."})
        if existing.status == Connection.Status.BLOCKED:
            raise ValidationError({"detail": "Unable to send connection request."})

    text = (message or "").strip()[:300]
    try:
        connection = Connection.objects.create(
            sender=sender,
            receiver=receiver,
            status=Connection.Status.PENDING,
            message=text,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "A connection request already exists."}
        ) from exc

    connection = Connection.objects.select_related(
        "sender", "receiver", "sender__profile", "receiver__profile"
    ).get(pk=connection.pk)
    from apps.notifications.signals import notify_connection_request

    notify_connection_request(actor=sender, connection=connection)
    return connection


def _get_pending_for_receiver(*, connection_id, receiver) -> Connection:
    try:
        connection = Connection.objects.select_related(
            "sender", "receiver", "sender__profile", "receiver__profile"
        ).get(pk=connection_id)
    except Connection.DoesNotExist as exc:
        raise NotFound("Connection request not found.") from exc

    if connection.receiver_id != receiver.id:
        raise PermissionDenied("Only the recipient can respond to this request.")
    if connection.status != Connection.Status.PENDING:
        raise ValidationError({"detail": "This request is no longer pending."})
    return connection


@transaction.atomic
def accept_connection_request(*, connection_id, actor) -> Connection:
    connection = _get_pending_for_receiver(connection_id=connection_id, receiver=actor)
    connection.status = Connection.Status.ACCEPTED
    connection.accepted_at = timezone.now()
    connection.save(update_fields=["status", "accepted_at", "updated_at"])
    from apps.notifications.signals import notify_connection_accepted

    notify_connection_accepted(actor=actor, connection=connection)
    return connection


@transaction.atomic
def reject_connection_request(*, connection_id, actor) -> Connection:
    connection = _get_pending_for_receiver(connection_id=connection_id, receiver=actor)
    connection.status = Connection.Status.REJECTED
    connection.save(update_fields=["status", "updated_at"])
    return connection


@transaction.atomic
def cancel_connection_request(*, connection_id, actor) -> Connection:
    try:
        connection = Connection.objects.select_related("sender", "receiver").get(
            pk=connection_id
        )
    except Connection.DoesNotExist as exc:
        raise NotFound("Connection request not found.") from exc

    if connection.sender_id != actor.id:
        raise PermissionDenied("Only the sender can cancel this request.")
    if connection.status != Connection.Status.PENDING:
        raise ValidationError({"detail": "This request is no longer pending."})

    connection.status = Connection.Status.CANCELLED
    connection.save(update_fields=["status", "updated_at"])
    return connection


@transaction.atomic
def remove_connection(*, actor, username: str) -> Connection:
    other = _get_active_user(username)
    connection = (
        Connection.objects.filter(
            Q(sender=actor, receiver=other) | Q(sender=other, receiver=actor),
            status=Connection.Status.ACCEPTED,
        )
        .select_related("sender", "receiver")
        .first()
    )
    if connection is None:
        raise NotFound("Connection not found.")

    connection.status = Connection.Status.REMOVED
    connection.save(update_fields=["status", "updated_at"])
    return connection


def are_connected(user_a, user_b) -> bool:
    if not user_a or not user_b:
        return False
    return Connection.objects.filter(
        Q(sender=user_a, receiver=user_b) | Q(sender=user_b, receiver=user_a),
        status=Connection.Status.ACCEPTED,
    ).exists()
