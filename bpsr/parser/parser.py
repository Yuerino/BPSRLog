from __future__ import annotations

from typing import TYPE_CHECKING

from bpsr.utils import ParseError

from .constants import MessageType
from .message import MESSAGE_TYPE_REGISTRY, Message

if TYPE_CHECKING:
    from bpsr.packet.game_packet import GamePacket


def parse_packet(packet: GamePacket, is_from_client: bool) -> Message:
    if packet.length < 6:
        raise ParseError(f"Packet too short: {packet.length}", packet.raw_data)

    if not isinstance(packet.msg_type, MessageType):
        raise ParseError(f"Unknown message type: {packet.msg_type}", packet.raw_data)

    msg_kwargs = {
        "msg_type": packet.msg_type,
        "is_from_client": is_from_client,
    }

    cls = MESSAGE_TYPE_REGISTRY.get(packet.msg_type)
    if cls is None:
        raise ParseError(f"No registered class for message type {packet.msg_type}", packet.raw_data)
    return cls.from_payload(packet.raw_data, packet.is_compressed, **msg_kwargs)


__all__ = ["parse_packet"]
