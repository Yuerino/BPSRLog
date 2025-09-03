from __future__ import annotations

import struct
from dataclasses import dataclass

from bpsr.utils import ParseError, decompress_zstd

from .constants import MessageType

MESSAGE_TYPE_REGISTRY: dict[MessageType, type[Message]] = {}


def register_message_type(msg_type: MessageType) -> callable:
    def decorator(cls: type[Message]) -> type[Message]:
        MESSAGE_TYPE_REGISTRY[msg_type] = cls
        return cls

    return decorator


@dataclass(slots=True, frozen=True)
class Message:
    msg_type: MessageType
    is_from_client: bool
    payload: bytes | None


@register_message_type(MessageType.CALL)
@dataclass(slots=True, frozen=True)
class CallMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> CallMessage:
        kwargs.setdefault("payload", None)
        return cls(**kwargs)


@register_message_type(MessageType.NOTIFY)
@dataclass(slots=True, frozen=True)
class NotifyMessage(Message):
    service_id: int
    stub_id: int
    method_id: int

    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> NotifyMessage:
        if len(payload) < 16:
            raise ParseError("Notify message packet too short", payload)

        service_id = struct.unpack("!Q", payload[:8])[0]
        stub_id = struct.unpack("!I", payload[8:12])[0]
        method_id = struct.unpack("!I", payload[12:16])[0]
        payload = payload[16:] if len(payload) > 16 else None

        kwargs.update({"service_id": service_id, "stub_id": stub_id, "method_id": method_id, "payload": payload})
        return cls(**kwargs)


@register_message_type(MessageType.RETURN)
@dataclass(slots=True, frozen=True)
class ReturnMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> ReturnMessage:
        kwargs.setdefault("payload", None)
        return cls(**kwargs)


@register_message_type(MessageType.ECHO)
@dataclass(slots=True, frozen=True)
class EchoMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> EchoMessage:
        kwargs.setdefault("payload", None)
        return cls(**kwargs)


@register_message_type(MessageType.FRAME_UP)
@dataclass(slots=True, frozen=True)
class FrameUpMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> FrameUpMessage:
        kwargs.setdefault("payload", None)
        return cls(**kwargs)


@register_message_type(MessageType.FRAME_DOWN)
@dataclass(slots=True, frozen=True)
class FrameDownMessage(Message):
    sequence_id: int
    nested_messages: list[Message]

    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> FrameDownMessage:
        kwargs.setdefault("payload", None)
        if len(payload) < 4:
            raise ParseError("FrameDown message packet too short", payload)

        sequence_id = struct.unpack("!I", payload[:4])[0]
        nested_messages: list[Message] = []

        is_from_client = kwargs.get("is_from_client", True)
        current_data = payload[4:]
        if is_compressed:
            current_data = decompress_zstd(current_data)

        while current_data and len(current_data) >= 6:
            try:
                from bpsr.packet.game_packet import GamePacket  # noqa: PLC0415

                nested_game_packet = GamePacket(current_data)
                if nested_game_packet.length > 0:
                    from .parser import parse_packet  # noqa: PLC0415

                    nested_messages.append(parse_packet(nested_game_packet, is_from_client))

                padding = b""
                if nested_game_packet.payload and nested_game_packet.length > 6:
                    _, padding = nested_game_packet.extract_padding(nested_game_packet.payload)
                current_data = padding if padding else b""
            except (ValueError, IndexError):
                break

        kwargs.update({"sequence_id": sequence_id, "nested_messages": nested_messages})
        return cls(**kwargs)


@register_message_type(MessageType.ACK_FRAME_UP)
@dataclass(slots=True, frozen=True)
class AckFrameUpMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> AckFrameUpMessage:
        kwargs.setdefault("payload", None)
        return cls(**kwargs)


@register_message_type(MessageType.ACK_FRAME_DOWN)
@dataclass(slots=True, frozen=True)
class AckFrameDownMessage(Message):
    @classmethod
    def from_payload(cls, payload, is_compressed, **kwargs) -> AckFrameDownMessage:
        kwargs["payload"] = payload
        return cls(**kwargs)


__all__ = ["Message", "NotifyMessage", "EchoMessage", "FrameUpMessage", "FrameDownMessage", "AckFrameUpMessage", "AckFrameDownMessage"]
