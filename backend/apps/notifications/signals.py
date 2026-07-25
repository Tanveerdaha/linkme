"""Signal receivers and domain notification helpers."""

from django.dispatch import receiver

from apps.messaging.signals import message_created_signal
from apps.notifications.models import Notification
from apps.notifications.tasks import enqueue_notification


def _message_should_notify(*, recipient, conversation_id) -> bool:
    """Notify only when recipient is offline or not viewing this conversation."""
    from apps.messaging import presence as messaging_presence

    viewing = messaging_presence.get_viewing_conversation(recipient.id)
    if viewing and str(viewing) == str(conversation_id):
        return False
    return True


@receiver(message_created_signal)
def on_message_created(sender, message, conversation, sender_user, **kwargs):
    from apps.messaging import selectors

    other = selectors.get_other_member(
        conversation=conversation, viewer=sender_user
    )
    if other is None:
        return
    recipient = other.user
    if not _message_should_notify(
        recipient=recipient, conversation_id=conversation.id
    ):
        return
    enqueue_notification(
        recipient=recipient,
        sender=sender_user,
        notification_type=Notification.NotificationType.MESSAGE_RECEIVED,
        object_type=Notification.ObjectType.CONVERSATION,
        object_id=str(conversation.id),
    )


def notify_post_reaction(*, actor, post) -> None:
    enqueue_notification(
        recipient=post.author,
        sender=actor,
        notification_type=Notification.NotificationType.POST_REACTION,
        object_type=Notification.ObjectType.POST,
        object_id=str(post.id),
    )


def notify_comment_on_post(*, actor, post, comment) -> None:
    enqueue_notification(
        recipient=post.author,
        sender=actor,
        notification_type=Notification.NotificationType.POST_COMMENT,
        object_type=Notification.ObjectType.POST,
        object_id=f"{post.id}|{comment.id}",
    )


def notify_comment_reply(*, actor, parent_comment, reply) -> None:
    enqueue_notification(
        recipient=parent_comment.author,
        sender=actor,
        notification_type=Notification.NotificationType.COMMENT_REPLY,
        object_type=Notification.ObjectType.POST,
        object_id=f"{parent_comment.post_id}|{reply.id}",
    )


def notify_comment_reaction(*, actor, comment) -> None:
    enqueue_notification(
        recipient=comment.author,
        sender=actor,
        notification_type=Notification.NotificationType.COMMENT_REACTION,
        object_type=Notification.ObjectType.POST,
        object_id=f"{comment.post_id}|{comment.id}",
    )


def notify_connection_request(*, actor, connection) -> None:
    enqueue_notification(
        recipient=connection.receiver,
        sender=actor,
        notification_type=Notification.NotificationType.CONNECTION_REQUEST,
        object_type=Notification.ObjectType.USER,
        object_id=actor.username,
    )


def notify_connection_accepted(*, actor, connection) -> None:
    enqueue_notification(
        recipient=connection.sender,
        sender=actor,
        notification_type=Notification.NotificationType.CONNECTION_ACCEPTED,
        object_type=Notification.ObjectType.USER,
        object_id=actor.username,
    )
