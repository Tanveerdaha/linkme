"""Profile completion scoring."""

from apps.profiles.models import Profile

# Weights must sum to 100.
COMPLETION_WEIGHTS = {
    "avatar": 20,
    "cover_image": 15,
    "headline": 15,
    "bio": 20,
    "location": 10,
    "website": 10,
    "interests": 10,
}


def _has_value(profile: Profile, field: str) -> bool:
    if field == "avatar":
        return bool(profile.avatar)
    if field == "cover_image":
        return bool(profile.cover_image)
    if field == "interests":
        interests = profile.interests or []
        return isinstance(interests, list) and len(interests) > 0
    value = getattr(profile, field, None)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def calculate_profile_completion(profile: Profile) -> dict:
    """
    Return completion percentage and missing field names.

    Example::
        {"percentage": 80, "missing": ["cover_image", "bio"]}
    """
    missing: list[str] = []
    earned = 0
    for field, weight in COMPLETION_WEIGHTS.items():
        if _has_value(profile, field):
            earned += weight
        else:
            missing.append(field)
    return {"percentage": earned, "missing": missing}
