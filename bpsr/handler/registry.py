from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..logutil import get_logger
from ..parser.constants import MessageType
from ..parser.message import Message, NotifyMessage

logger = get_logger("HandlerRegistry")

HandlerFunc = Callable[[Message], Any]
NotifyHandlerFunc = Callable[[NotifyMessage], Any]

_message_handlers: dict[MessageType, HandlerFunc] = {}
_notify_handlers: dict[tuple[int, int], NotifyHandlerFunc] = {}


def register_message_handler(msg_type: MessageType) -> Callable[[HandlerFunc], HandlerFunc]:
    def decorator(handler: HandlerFunc) -> HandlerFunc:
        if msg_type in _message_handlers:
            logger.warning(f"Overriding existing handler for message type {msg_type.name}")

        _message_handlers[msg_type] = handler
        return handler

    return decorator


def register_notify_handler(service_id: int, method_id: int) -> Callable[[NotifyHandlerFunc], NotifyHandlerFunc]:
    def decorator(handler: NotifyHandlerFunc) -> NotifyHandlerFunc:
        key = (service_id, method_id)
        if key in _notify_handlers:
            logger.warning(f"Overriding existing handler for service 0x{service_id:016X}, method 0x{method_id:08X}")

        _notify_handlers[key] = handler
        return handler

    return decorator


def get_message_handler(msg_type: MessageType) -> HandlerFunc | None:
    return _message_handlers.get(msg_type)


def get_notify_handler(service_id: int, method_id: int) -> NotifyHandlerFunc | None:
    return _notify_handlers.get((service_id, method_id))


def handle_message(message: Message) -> bool:
    if isinstance(message, NotifyMessage):
        notify_handler = get_notify_handler(message.service_id, message.method_id)
        if not notify_handler:
            logger.debug(f"No Notify handler for service 0x{message.service_id:016X}, method 0x{message.method_id:08X}")
            return

        try:
            notify_handler(message)
        except Exception as e:
            logger.error(f"Error in Notify handler for service 0x{message.service_id:016X}, " f"method 0x{message.method_id:08X}: {e}")
    else:
        handler = get_message_handler(message.msg_type)
        if not handler:
            logger.debug(f"No handler for message type {message.msg_type.name}")
            return

        try:
            handler(message)
        except Exception as e:
            logger.error(f"Error in message handler for {message.msg_type.name}: {e}")


__all__ = [
    "register_message_handler",
    "register_notify_handler",
    "get_message_handler",
    "get_notify_handler",
    "handle_message",
]
