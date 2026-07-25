"""Permissions for the reactions app."""

from apps.posts.permissions import IsAuthenticatedVerified

# Authenticated + verified users may react.
CanReact = IsAuthenticatedVerified
