"""Rate limiting for social / safety actions."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class CommentCreateThrottle(UserRateThrottle):
    scope = "comment_create"


class MessageSendThrottle(UserRateThrottle):
    scope = "message_send"


class ReportCreateThrottle(UserRateThrottle):
    scope = "report_create"


class BlockActionThrottle(UserRateThrottle):
    scope = "block_action"


class AuthLoginBurstThrottle(AnonRateThrottle):
    scope = "auth_login"
