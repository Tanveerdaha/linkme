"""PostgreSQL full-text user search."""

from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q, QuerySet

from apps.profiles.models import Profile

User = get_user_model()


def search_users(
    *,
    q: str = "",
    location: str | None = None,
    interest: str | None = None,
    viewer=None,
) -> QuerySet:
    """
    Search public profiles by username, name, headline, bio, location, interests.

    Uses PostgreSQL full-text search when ``q`` is provided; falls back to
    icontains filters for short/partial matches.
    """
    qs = (
        Profile.objects.select_related("user")
        .filter(
            user__is_active=True,
            user__is_verified=True,
            profile_visibility=Profile.Visibility.PUBLIC,
        )
        .order_by("-updated_at")
    )

    # Owners can find themselves even if private when searching while logged in —
    # but discovery should stay public-only for MVP.

    if location:
        qs = qs.filter(location__icontains=location.strip())

    if interest:
        # JSONField contains — PostgreSQL supports __contains for lists.
        qs = qs.filter(interests__icontains=interest.strip())

    query = (q or "").strip()
    if not query:
        return qs

    # Full-text vector across user + profile text fields.
    vector = (
        SearchVector("user__username", weight="A")
        + SearchVector("user__first_name", weight="A")
        + SearchVector("user__last_name", weight="A")
        + SearchVector("headline", weight="B")
        + SearchVector("bio", weight="C")
        + SearchVector("location", weight="B")
    )
    search_query = SearchQuery(query)
    ranked = (
        qs.annotate(rank=SearchRank(vector, search_query))
        .filter(rank__gte=0.01)
        .order_by("-rank", "-updated_at")
    )

    # Also include simple icontains matches (usernames / partials FTS may miss).
    icontains_q = Q(
        user__username__icontains=query
    ) | Q(user__first_name__icontains=query) | Q(
        user__last_name__icontains=query
    ) | Q(headline__icontains=query) | Q(bio__icontains=query) | Q(
        location__icontains=query
    )

    # Union-style: prefer ranked FTS results, then fill with icontains.
    fts_ids = list(ranked.values_list("pk", flat=True)[:50])
    extra = qs.filter(icontains_q).exclude(pk__in=fts_ids)[:50]

    # Preserve rank order then extras.
    ordered_ids = fts_ids + list(extra.values_list("pk", flat=True))
    if not ordered_ids:
        return qs.none()

    preserved = {pk: index for index, pk in enumerate(ordered_ids)}
    results = list(qs.filter(pk__in=ordered_ids))
    results.sort(key=lambda p: preserved.get(p.pk, 9999))
    # Return as queryset-like list handled by view — wrap via filter for pagination.
    # For DRF pagination we need a queryset; use pk__in with Case/When ordering.
    from django.db.models import Case, IntegerField, When

    whens = [When(pk=pk, then=pos) for pos, pk in enumerate(ordered_ids)]
    return qs.filter(pk__in=ordered_ids).annotate(
        search_order=Case(*whens, output_field=IntegerField())
    ).order_by("search_order")
