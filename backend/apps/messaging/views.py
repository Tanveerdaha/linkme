"""API views for direct messaging."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messaging import presence, selectors, services
from apps.messaging.models import Message, MessageStatus
from apps.messaging.pagination import ConversationPagination, MessageCursorPagination
from apps.messaging.permissions import IsMessagingUser
from apps.messaging.serializers import (
    ConversationDetailSerializer,
    ConversationListItemSerializer,
    CreateConversationSerializer,
    MessageSerializer,
    MuteConversationSerializer,
    SendMessageSerializer,
)


def _avatar_url(profile, request) -> str | None:
    if not profile or not profile.avatar:
        return None
    url = profile.avatar.url
    return request.build_absolute_uri(url) if request else url


def _participant_payload(user, request) -> dict:
    profile = getattr(user, "profile", None)
    return {
        "username": user.username,
        "name": user.full_name,
        "avatar": _avatar_url(profile, request),
        "headline": getattr(profile, "headline", "") or "",
        "is_online": presence.is_online(user.id),
    }


def _serialize_conversation_list_item(conversation, viewer, request) -> dict:
    other = selectors.get_other_member(conversation=conversation, viewer=viewer)
    membership = selectors.get_membership(conversation=conversation, user=viewer)
    preview = getattr(conversation, "preview_content", None)
    preview_type = getattr(conversation, "preview_type", None)
    if not preview:
        if preview_type == Message.MessageType.IMAGE:
            preview = "Sent an image"
        elif preview_type == Message.MessageType.VIDEO:
            preview = "Sent a video"
        elif preview_type == Message.MessageType.FILE:
            preview = "Sent a file"
        elif preview_type == Message.MessageType.VOICE:
            preview = "Voice message"
        elif preview_type == Message.MessageType.LINK:
            preview = "Shared a link"
    return {
        "id": conversation.id,
        "participant": _participant_payload(other.user, request) if other else None,
        "last_message": preview,
        "last_message_at": conversation.last_message_at,
        "unread_count": selectors.count_unread(conversation=conversation, user=viewer),
        "is_muted": bool(membership and membership.is_muted),
    }


def _serialize_conversation_detail(conversation, viewer, request) -> dict:
    other = selectors.get_other_member(conversation=conversation, viewer=viewer)
    membership = selectors.get_membership(conversation=conversation, user=viewer)
    return {
        "id": conversation.id,
        "participant": _participant_payload(other.user, request) if other else None,
        "created_at": conversation.created_at,
        "is_muted": bool(membership and membership.is_muted),
    }


def _message_status_for_viewer(message: Message, viewer) -> str | None:
    if message.is_deleted:
        return None
    statuses = list(message.statuses.all())
    if message.sender_id == viewer.id:
        # Sender sees recipient delivery/read status.
        for s in statuses:
            if s.user_id != viewer.id:
                return s.status
        return MessageStatus.Status.SENT
    for s in statuses:
        if s.user_id == viewer.id:
            return s.status
    return None


def _serialize_message(message: Message, viewer, request) -> dict:
    attachment = None
    if message.attachment and not message.is_deleted:
        url = message.attachment.url
        attachment = request.build_absolute_uri(url) if request else url
    return {
        "id": message.id,
        "sender": message.sender.username,
        "content": "" if message.is_deleted else message.content,
        "message_type": message.message_type,
        "attachment": attachment,
        "metadata": {} if message.is_deleted else (message.metadata or {}),
        "created_at": message.created_at,
        "updated_at": message.updated_at,
        "is_deleted": message.is_deleted,
        "status": _message_status_for_viewer(message, viewer),
    }


class ConversationListCreateView(APIView):
    """GET/POST /api/v1/messages/conversations/"""

    permission_classes = [IsMessagingUser]
    pagination_class = ConversationPagination

    @extend_schema(
        responses={200: ConversationListItemSerializer(many=True)},
        tags=["messages"],
        summary="List conversations",
    )
    def get(self, request):
        qs = selectors.get_user_conversations(user=request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        results = [
            _serialize_conversation_list_item(c, request.user, request) for c in page
        ]
        return paginator.get_paginated_response(results)

    @extend_schema(
        request=CreateConversationSerializer,
        responses={
            200: ConversationDetailSerializer,
            201: ConversationDetailSerializer,
        },
        tags=["messages"],
        summary="Create or get direct conversation",
    )
    def post(self, request):
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]

        existing = None
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other = User.objects.filter(
            username__iexact=username, is_active=True, is_verified=True
        ).first()
        if other:
            existing = selectors.get_direct_conversation_between(
                user_a=request.user, user_b=other
            )

        conversation = services.get_or_create_direct_conversation(
            user=request.user, username=username
        )
        payload = _serialize_conversation_detail(conversation, request.user, request)
        code = status.HTTP_200_OK if existing else status.HTTP_201_CREATED
        return Response(payload, status=code)


class ConversationDetailView(APIView):
    """GET /api/v1/messages/conversations/{id}/"""

    permission_classes = [IsMessagingUser]

    @extend_schema(
        responses={200: ConversationDetailSerializer},
        tags=["messages"],
        summary="Conversation detail",
    )
    def get(self, request, conversation_id):
        conversation = selectors.get_conversation_for_user(
            conversation_id=conversation_id, user=request.user
        )
        if conversation is None:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            _serialize_conversation_detail(conversation, request.user, request)
        )


class ConversationMuteView(APIView):
    """PATCH /api/v1/messages/conversations/{id}/mute/"""

    permission_classes = [IsMessagingUser]

    @extend_schema(
        request=MuteConversationSerializer,
        responses={200: ConversationDetailSerializer},
        tags=["messages"],
        summary="Mute or unmute a conversation",
    )
    def patch(self, request, conversation_id):
        serializer = MuteConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.set_conversation_muted(
            user=request.user,
            conversation_id=conversation_id,
            is_muted=serializer.validated_data["is_muted"],
        )
        conversation = selectors.get_conversation_for_user(
            conversation_id=conversation_id, user=request.user
        )
        return Response(
            _serialize_conversation_detail(conversation, request.user, request)
        )


class ConversationMessagesView(APIView):
    """GET/POST /api/v1/messages/conversations/{id}/messages/"""

    permission_classes = [IsMessagingUser]
    pagination_class = MessageCursorPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_throttles(self):
        if self.request.method == "POST":
            from apps.moderation.throttling import MessageSendThrottle

            return [MessageSendThrottle()]
        return []

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: MessageSerializer(many=True)},
        tags=["messages"],
        summary="Message history (cursor paginated)",
    )
    def get(self, request, conversation_id):
        conversation = selectors.get_conversation_for_user(
            conversation_id=conversation_id, user=request.user
        )
        if conversation is None:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = selectors.get_conversation_messages(conversation=conversation)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        results = [_serialize_message(m, request.user, request) for m in page]
        return paginator.get_paginated_response(results)

    @extend_schema(
        request=SendMessageSerializer,
        responses={201: MessageSerializer},
        tags=["messages"],
        summary="Send a message (REST fallback)",
    )
    def post(self, request, conversation_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = services.send_message(
            sender=request.user,
            conversation_id=conversation_id,
            content=serializer.validated_data.get("content", ""),
            attachment=serializer.validated_data.get("attachment"),
            message_type=serializer.validated_data.get("message_type"),
            metadata=serializer.validated_data.get("metadata") or {},
        )
        from apps.messaging.broadcast import broadcast_message

        broadcast_message(message)
        return Response(
            _serialize_message(message, request.user, request),
            status=status.HTTP_201_CREATED,
        )


class MessageDeleteView(APIView):
    """DELETE /api/v1/messages/{id}/"""

    permission_classes = [IsMessagingUser]

    @extend_schema(
        responses={204: None},
        tags=["messages"],
        summary="Soft-delete own message",
    )
    def delete(self, request, message_id):
        services.delete_message(actor=request.user, message_id=message_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
