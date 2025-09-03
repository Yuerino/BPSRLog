"""
Handler system for processing different message types and service methods.

This module provides a decorator-based system for registering handlers
for specific message types, services, and methods.
"""

from .registry import get_message_handler, get_notify_handler, handle_message, register_message_handler, register_notify_handler

__all__ = [
    "register_notify_handler",
    "register_message_handler",
    "get_notify_handler",
    "get_message_handler",
    "handle_message",
]
