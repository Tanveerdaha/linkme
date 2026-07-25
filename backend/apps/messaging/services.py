"""Domain services for direct messaging between accepted connections."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.messaging import selectors
from apps.messaging.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageStatus,
)
from apps.messaging.signals import message_created_signal, message_read_signal

User = get_user_model()


def _get_active_user(username: str):
    return get_object_or_404(
        User.objects.select_related("profile"),
        username__iexact=username,
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )


def _require_connected(*, user_a, user_b) -> None:
    from apps.privacy.services import can_message

    if not can_message(sender=user_a, recipient=user_b):
        raise PermissionDenied("You cannot message this user.")


@transaction.atomic
def create_conversation(*, creator, username: str) -> Conversation:
    """Create a DIRECT conversation with ``username`` (must be connected)."""
    return get_or_create_direct_conversation(user=creator, username=username)


@transaction.atomic
def get_or_create_direct_conversation(*, user, username: str) -> Conversation:
    if user.username.lower() == username.lower():
        raise ValidationError({"detail": "You cannot message yourself."})

    other = _get_active_user(username)
    _require_connected(user_a=user, user_b=other)

    existing = selectors.get_direct_conversation_between(user_a=user, user_b=other)
    if existing is not None:
        return existing

    conversation = Conversation.objects.create(
        conversation_type=Conversation.ConversationType.DIRECT,
    )
    ConversationMember.objects.bulk_create(
        [
            ConversationMember(conversation=conversation, user=user),
            ConversationMember(conversation=conversation, user=other),
        ]
    )
    return selectors.get_conversation_for_user(
        conversation_id=conversation.id, user=user
    )


@transaction.atomic
def send_message(
    *,
    sender,
    conversation_id,
    content: str = "",
    attachment=None,
    message_type: str | None = None,
    metadata: dict | None = None,
) -> Message:
    from apps.messaging.validators import (
        infer_message_type_from_file,
        validate_message_attachment,
    )
    from apps.moderation.blocks import assert_user_can_act

    assert_user_can_act(sender)
    conversation = selectors.get_conversation_for_user(
        conversation_id=conversation_id, user=sender
    )
    if conversation is None:
        raise NotFound("Conversation not found.")

    other = selectors.get_other_member(conversation=conversation, viewer=sender)
    if other is None:
        raise ValidationError({"detail": "Invalid conversation members."})

    # Re-check connection is still accepted.
    _require_connected(user_a=sender, user_b=other.user)

    text = (content or "").strip()
    meta = dict(metadata or {})
    resolved_type = (message_type or "").upper() or None

    if attachment is not None:
        resolved_type = resolved_type or infer_message_type_from_file(attachment)
        if resolved_type not in {
            Message.MessageType.IMAGE,
            Message.MessageType.VIDEO,
            Message.MessageType.FILE,
            Message.MessageType.VOICE,
        }:
            raise ValidationError(
                {"message_type": "Invalid message type for attachment."}
            )
        try:
            validate_message_attachment(attachment, resolved_type)
        except Exception as exc:
            from django.core.exceptions import ValidationError as DjangoValidationError

            if isinstance(exc, DjangoValidationError):
                raise ValidationError({"attachment": list(exc.messages)}) from exc
            raise
        if not meta.get("filename"):
            meta["filename"] = getattr(attachment, "name", "") or ""
        if resolved_type == Message.MessageType.FILE and not text:
            text = meta.get("filename") or "File"
    elif resolved_type == Message.MessageType.LINK:
        url = (meta.get("url") or text or "").strip()
        if not url:
            raise ValidationError({"metadata": "A URL is required for link messages."})
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValidationError(
                {"metadata": "URL must start with http:// or https://."}
            )
        meta["url"] = url
        if not text:
            text = url
    else:
        resolved_type = Message.MessageType.TEXT
        if not text:
            raise ValidationError({"content": "Message content is required."})

    if len(text) > 5000:
        raise ValidationError({"content": "Message is too long (max 5000 characters)."})

    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=text,
        message_type=resolved_type,
        attachment=attachment,
        metadata=meta,
    )

    MessageStatus.objects.create(
        message=message,
        user=other.user,
        status=MessageStatus.Status.SENT,
    )

    now = timezone.now()
    Conversation.objects.filter(pk=conversation.pk).update(
        last_message_at=now,
        updated_at=now,
    )

    message_created_signal.send(
        sender=Message,
        message=message,
        conversation=conversation,
        sender_user=sender,
    )

    return (
        Message.objects.select_related("sender", "sender__profile")
        .prefetch_related("statuses")
        .get(pk=message.pk)
    )


@transaction.atomic
def mark_message_read(*, reader, message_id) -> MessageStatus:
    message = (
        Message.objects.select_related("conversation", "sender")
        .filter(pk=message_id)
        .first()
    )
    if message is None:
        raise NotFound("Message not found.")

    if not selectors.user_is_member(
        conversation_id=message.conversation_id, user=reader
    ):
        raise PermissionDenied("You are not a member of this conversation.")

    if message.sender_id == reader.id:
        raise ValidationError({"detail": "Cannot mark your own message as read."})

    status_obj, _ = MessageStatus.objects.get_or_create(
        message=message,
        user=reader,
        defaults={"status": MessageStatus.Status.READ},
    )
    if status_obj.status != MessageStatus.Status.READ:
        status_obj.status = MessageStatus.Status.READ
        status_obj.save(update_fields=["status", "updated_at"])

    ConversationMember.objects.filter(
        conversation_id=message.conversation_id,
        user=reader,
    ).update(last_read_at=timezone.now())

    message_read_signal.send(
        sender=MessageStatus,
        message=message,
        reader=reader,
        status=status_obj,
    )
    return status_obj


@transaction.atomic
def mark_conversation_read(*, reader, conversation_id) -> int:
    """Mark all unread messages in a conversation as READ. Returns count updated."""
    conversation = selectors.get_conversation_for_user(
        conversation_id=conversation_id, user=reader
    )
    if conversation is None:
        raise NotFound("Conversation not found.")

    now = timezone.now()
    ConversationMember.objects.filter(conversation=conversation, user=reader).update(
        last_read_at=now
    )

    statuses = MessageStatus.objects.filter(
        message__conversation=conversation,
        user=reader,
    ).exclude(status=MessageStatus.Status.READ)

    updated = statuses.update(status=MessageStatus.Status.READ)
    return updated


@transaction.atomic
def mark_message_delivered(*, recipient, message_id) -> MessageStatus | None:
    status_obj = (
        MessageStatus.objects.select_related("message")
        .filter(message_id=message_id, user=recipient)
        .first()
    )
    if status_obj is None:
        return None
    if status_obj.status == MessageStatus.Status.SENT:
        status_obj.status = MessageStatus.Status.DELIVERED
        status_obj.save(update_fields=["status", "updated_at"])
    return status_obj


@transaction.atomic
def delete_message(*, actor, message_id) -> Message:
    message = Message.objects.filter(pk=message_id).first()
    if message is None:
        raise NotFound("Message not found.")

    if message.sender_id != actor.id:
        raise PermissionDenied("You can only delete your own messages.")

    if not selectors.user_is_member(
        conversation_id=message.conversation_id, user=actor
    ):
        raise PermissionDenied("You are not a member of this conversation.")

    if not message.is_deleted:
        message.is_deleted = True
        message.save(update_fields=["is_deleted", "updated_at"])
    return message


@transaction.atomic
def set_conversation_muted(
    *, user, conversation_id, is_muted: bool
) -> ConversationMember:
    membership = ConversationMember.objects.filter(
        conversation_id=conversation_id, user=user
    ).first()
    if membership is None:
        raise NotFound("Conversation not found.")
    membership.is_muted = is_muted
    membership.save(update_fields=["is_muted"])
    return membership
