"""Throttling for connection request abuse prevention."""

from rest_framework.throttling import UserRateThrottle


class ConnectionRequestThrottle(UserRateThrottle):
    """Limit how quickly a user can send connection requests."""

    scope = "connection_request"
