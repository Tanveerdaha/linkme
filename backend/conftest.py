"""
Pytest configuration for LinkMe backend tests.
"""

import pytest


@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(db):
    """Allow database access in all tests by default."""
    pass


@pytest.fixture(autouse=True)
def _disable_throttling(settings):
    """Avoid cross-test 429s from scoped auth throttles."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            "anon": "10000/min",
            "user": "10000/min",
            "auth_signup": "1000/min",
            "auth_login": "1000/min",
            "auth_google": "1000/min",
            "auth_phone_send": "1000/min",
            "auth_phone_verify": "1000/min",
            "auth_password_reset": "1000/min",
            "posts_create": "1000/min",
            "feed_read": "1000/min",
            "media_upload": "1000/min",
            "connection_request": "1000/min",
            "comment_create": "1000/min",
            "message_send": "1000/min",
            "report_create": "1000/min",
            "block_action": "1000/min",
        },
    }
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.REDIS_BLOOM_ENABLED = True
