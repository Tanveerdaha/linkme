"""Read selectors for messaging."""

from django.db.models import Count, OuterRef, Prefetch, QuerySet, Subquery
from django.db.models.functions import Coalesce

from apps.messaging.models import Conversation, ConversationMember, Message


def get_user_conversations(*, user) -> QuerySet:
    """Conversations the user belongs to, newest activity first."""
    last_message = (
        Message.objects.filter(conversation_id=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("content")[:1]
    )
    last_message_type = (
        Message.objects.filter(conversation_id=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("message_type")[:1]
    )
    last_message_id = (
        Message.objects.filter(conversation_id=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("id")[:1]
    )
    last_sender = (
        Message.objects.filter(conversation_id=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("sender__username")[:1]
    )

    return (
        Conversation.objects.filter(members__user=user)
        .distinct()
        .annotate(
            preview_content=Subquery(last_message),
            preview_type=Subquery(last_message_type),
            preview_id=Subquery(last_message_id),
            preview_sender=Subquery(last_sender),
        )
        .prefetch_related(
            Prefetch(
                "members",
                queryset=ConversationMember.objects.select_related(
                    "user", "user__profile"
                ),
            )
        )
        .order_by(
            Coalesce("last_message_at", "updated_at").desc(),
            "-updated_at",
        )
    )


def get_conversation_for_user(*, conversation_id, user) -> Conversation | None:
    return (
        Conversation.objects.filter(id=conversation_id, members__user=user)
        .prefetch_related(
            Prefetch(
                "members",
                queryset=ConversationMember.objects.select_related(
                    "user", "user__profile"
                ),
            )
        )
        .first()
    )


def get_conversation_messages(*, conversation) -> QuerySet:
    return (
        Message.objects.filter(conversation=conversation)
        .select_related("sender", "sender__profile")
        .prefetch_related("statuses")
        .order_by("-created_at", "-id")
    )


def get_direct_conversation_between(*, user_a, user_b) -> Conversation | None:
    """Return existing DIRECT conversation with exactly these two members."""
    ids_a = ConversationMember.objects.filter(user=user_a).values_list(
        "conversation_id", flat=True
    )
    ids_b = ConversationMember.objects.filter(user=user_b).values_list(
        "conversation_id", flat=True
    )
    return (
        Conversation.objects.filter(
            conversation_type=Conversation.ConversationType.DIRECT,
            id__in=ids_a,
        )
        .filter(id__in=ids_b)
        .annotate(member_count=Count("members", distinct=True))
        .filter(member_count=2)
        .prefetch_related(
            Prefetch(
                "members",
                queryset=ConversationMember.objects.select_related(
                    "user", "user__profile"
                ),
            )
        )
        .first()
    )


def get_other_member(*, conversation, viewer) -> ConversationMember | None:
    return (
        ConversationMember.objects.filter(conversation=conversation)
        .exclude(user=viewer)
        .select_related("user", "user__profile")
        .first()
    )


def user_is_member(*, conversation_id, user) -> bool:
    return ConversationMember.objects.filter(
        conversation_id=conversation_id, user=user
    ).exists()


def get_membership(*, conversation, user) -> ConversationMember | None:
    return (
        ConversationMember.objects.filter(conversation=conversation, user=user)
        .select_related("user")
        .first()
    )


def count_unread(*, conversation, user) -> int:
    membership = get_membership(conversation=conversation, user=user)
    if membership is None:
        return 0
    qs = Message.objects.filter(
        conversation=conversation,
        is_deleted=False,
    ).exclude(sender=user)
    if membership.last_read_at:
        qs = qs.filter(created_at__gt=membership.last_read_at)
    return qs.count()
