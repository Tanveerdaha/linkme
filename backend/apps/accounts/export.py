"""User data export ZIP generation."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

User = get_user_model()


def export_user_data(user) -> bytes:
    """
    Build a ZIP archive of the user's portable data.

    Includes: profile, posts, comments, message metadata, connections.
    """
    profile_data = _export_profile(user)
    posts_data = _export_posts(user)
    comments_data = _export_comments(user)
    messages_data = _export_message_metadata(user)
    connections_data = _export_connections(user)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("profile.json", json.dumps(profile_data, indent=2, default=str))
        zf.writestr("posts.json", json.dumps(posts_data, indent=2, default=str))
        zf.writestr("comments.json", json.dumps(comments_data, indent=2, default=str))
        zf.writestr(
            "messages_metadata.json",
            json.dumps(messages_data, indent=2, default=str),
        )
        zf.writestr(
            "connections.json",
            json.dumps(connections_data, indent=2, default=str),
        )
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "exported_at": timezone.now().isoformat(),
                    "user_id": str(user.id),
                    "username": user.username,
                    "format_version": "1.0",
                },
                indent=2,
            ),
        )
    return buffer.getvalue()


def generate_and_store_export(export_request) -> None:
    """Generate ZIP and attach it to the DataExportRequest."""
    from apps.moderation.models import DataExportRequest

    export_request.status = DataExportRequest.Status.PROCESSING
    export_request.save(update_fields=["status"])

    try:
        data = export_user_data(export_request.user)
        filename = (
            f"linkme-export-{export_request.user.username}-{export_request.id}.zip"
        )
        export_request.file.save(filename, ContentFile(data), save=False)
        export_request.status = DataExportRequest.Status.READY
        export_request.completed_at = timezone.now()
        export_request.expires_at = timezone.now() + timedelta(days=7)
        export_request.error_message = ""
        export_request.save()
    except Exception as exc:  # noqa: BLE001
        export_request.status = DataExportRequest.Status.FAILED
        export_request.error_message = str(exc)[:500]
        export_request.save(update_fields=["status", "error_message"])
        raise


def _export_profile(user) -> dict:
    profile = getattr(user, "profile", None)
    if profile is None:
        return {"username": user.username, "email": user.email}
    return {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": profile.bio,
        "headline": profile.headline,
        "location": profile.location,
        "website": profile.website,
        "interests": profile.interests,
        "pronouns": profile.pronouns,
        "profile_visibility": profile.profile_visibility,
        "connection_visibility": profile.connection_visibility,
        "created_at": profile.created_at,
    }


def _export_posts(user) -> list:
    from apps.posts.models import Post

    posts = Post.objects.filter(author=user).exclude(status=Post.Status.DELETED)
    return [
        {
            "id": str(p.id),
            "content": p.content,
            "visibility": p.visibility,
            "status": p.status,
            "published_at": p.published_at,
            "created_at": p.created_at,
        }
        for p in posts.iterator()
    ]


def _export_comments(user) -> list:
    from apps.comments.models import Comment

    comments = Comment.objects.filter(author=user).exclude(
        status=Comment.Status.DELETED
    )
    return [
        {
            "id": str(c.id),
            "post_id": str(c.post_id),
            "content": c.content,
            "created_at": c.created_at,
        }
        for c in comments.iterator()
    ]


def _export_message_metadata(user) -> list:
    from apps.messaging.models import Message

    messages = Message.objects.filter(sender=user, is_deleted=False)
    return [
        {
            "id": str(m.id),
            "conversation_id": str(m.conversation_id),
            "message_type": m.message_type,
            "created_at": m.created_at,
            "has_attachment": bool(m.attachment),
        }
        for m in messages.iterator()
    ]


def _export_connections(user) -> list:
    from apps.network.models import Connection
    from django.db.models import Q

    connections = Connection.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status=Connection.Status.ACCEPTED,
    ).select_related("sender", "receiver")
    results = []
    for conn in connections:
        other = conn.receiver if conn.sender_id == user.id else conn.sender
        results.append(
            {
                "username": other.username,
                "connected_at": conn.accepted_at or conn.created_at,
            }
        )
    return results
