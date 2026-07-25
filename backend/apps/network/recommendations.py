"""Network discovery suggestions (non-AI heuristics)."""

from datetime import timedelta

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.network.models import Connection
from apps.network.selectors import get_connected_user_ids
from apps.posts.models import Post
from apps.profiles.models import Profile


def get_network_suggestions(*, viewer, limit: int = 20) -> list[dict]:
    """
    Suggest people to connect with.

    Priority:
    1. Complete profiles
    2. Active users (recent posts)
    3. Similar interests
    4. Recent users

    Excludes self, already-connected, pending requests, and blocked pairs.
    """
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return []

    connected_ids = get_connected_user_ids(viewer)
    pending_ids = set(
        Connection.objects.filter(
            Q(sender=viewer) | Q(receiver=viewer),
            status=Connection.Status.PENDING,
        ).values_list("sender_id", "receiver_id")
    )
    exclude_ids = {viewer.id} | connected_ids
    for sender_id, receiver_id in pending_ids:
        exclude_ids.add(sender_id)
        exclude_ids.add(receiver_id)

    blocked_pairs = Connection.objects.filter(
        Q(sender=viewer) | Q(receiver=viewer),
        status=Connection.Status.BLOCKED,
    ).values_list("sender_id", "receiver_id")
    for sender_id, receiver_id in blocked_pairs:
        exclude_ids.add(sender_id if sender_id != viewer.id else receiver_id)

    recent_cutoff = timezone.now() - timedelta(days=30)
    viewer_interests = set(viewer.profile.interests or []) if hasattr(viewer, "profile") else set()

    qs = (
        Profile.objects.select_related("user")
        .filter(
            user__is_active=True,
            user__is_verified=True,
            profile_visibility=Profile.Visibility.PUBLIC,
        )
        .exclude(user_id__in=exclude_ids)
        .annotate(
            recent_posts=Count(
                "user__posts",
                filter=Q(
                    user__posts__status=Post.Status.PUBLISHED,
                    user__posts__published_at__gte=recent_cutoff,
                ),
                distinct=True,
            ),
            total_posts=Count(
                "user__posts",
                filter=Q(user__posts__status=Post.Status.PUBLISHED),
                distinct=True,
            ),
        )
        .order_by("-recent_posts", "-total_posts", "-updated_at")[: limit * 3]
    )

    results: list[dict] = []
    for profile in qs:
        reason = "Suggested for you"
        interests = set(profile.interests or [])
        shared = viewer_interests & interests
        if shared:
            reason = "Similar interests"
        elif profile.avatar and profile.headline:
            reason = "Complete profile"
        elif profile.recent_posts > 0:
            reason = "Active on LinkMe"
        elif (timezone.now() - profile.user.created_at).days < 14:
            reason = "Recently joined"

        results.append(
            {
                "profile": profile,
                "reason": reason,
                "shared_interests": len(shared),
            }
        )

    # Prefer similar interests, then complete/active.
    results.sort(
        key=lambda item: (
            item["shared_interests"],
            1 if item["reason"] == "Complete profile" else 0,
            item["profile"].recent_posts,
        ),
        reverse=True,
    )
    return results[:limit]
