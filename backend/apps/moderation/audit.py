"""Audit logging helpers."""

from apps.moderation.models import AuditLog


def log_audit(
    *,
    user=None,
    action: str,
    object_type: str = "",
    object_id: str = "",
    metadata: dict | None = None,
) -> AuditLog:
    """Persist an audit log entry. Never raises to callers."""
    try:
        return AuditLog.objects.create(
            user=user if user is not None and getattr(user, "is_authenticated", True) else None,
            action=action,
            object_type=object_type or "",
            object_id=str(object_id) if object_id else "",
            metadata=metadata or {},
        )
    except Exception:  # noqa: BLE001 — audit must not break primary flows
        return None  # type: ignore[return-value]
