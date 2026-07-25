"""Signals for messaging events — consumed by future notification system."""

from django.dispatch import Signal

# Fired after a message is persisted. Args: message, conversation, sender.
message_created_signal = Signal()

# Fired after a message is marked read. Args: message, reader, status.
message_read_signal = Signal()
