from __future__ import annotations

from bpsr.utils import hex_preview

from ..handler import register_message_handler
from ..logutil import get_logger
from ..parser.constants import MessageType
from ..parser.message import AckFrameDownMessage, AckFrameUpMessage, EchoMessage, FrameDownMessage, FrameUpMessage

logger = get_logger("GeneralHandlers")


@register_message_handler(MessageType.ECHO)
def handle_echo(message: EchoMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    logger.debug(f"[{direction}] ECHO message")


@register_message_handler(MessageType.FRAME_UP)
def handle_frame_up(message: FrameUpMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    logger.debug(f"[{direction}] FRAME_UP message")


@register_message_handler(MessageType.FRAME_DOWN)
def handle_frame_down(message: FrameDownMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    nested_count = len(message.nested_messages) if message.nested_messages else 0

    logger.debug(f"[{direction}] FRAME_DOWN: seq={message.sequence_id}, " f"nested_messages={nested_count}")

    if message.nested_messages:
        from . import handle_message  # noqa: PLC0415

        for nested_msg in message.nested_messages:
            handle_message(nested_msg)


@register_message_handler(MessageType.ACK_FRAME_UP)
def handle_ack_frame_up(message: AckFrameUpMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    logger.debug(f"[{direction}] ACK_FRAME_UP message")


@register_message_handler(MessageType.ACK_FRAME_DOWN)
def handle_ack_frame_down(message: AckFrameDownMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    logger.debug(
        f"[{direction}] ACK_FRAME_DOWN message: {len(message.payload) if message.payload else 0} bytes, preview = {hex_preview(message.payload, 128) if message.payload else 'N/A'}"
    )
