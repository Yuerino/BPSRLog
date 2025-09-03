from __future__ import annotations

import struct

from scapy.all import TCP
from scapy.fields import IntField, ShortField, StrLenField
from scapy.packet import Packet

from bpsr.packet.capture_utils import is_payload_game_packet
from bpsr.parser.constants import MessageType

MAX_PACKET_SIZE = 10 * 1024 * 1024

COMPRESSION_FLAG = 0x8000
MESSAGE_TYPE_MASK = 0x7FFF


class GamePacket(Packet):
    name = "GamePacket"
    fields_desc = [
        IntField("length", 0),
        ShortField("raw_msg_type", 0),
        StrLenField("raw_data", b"", length_from=lambda pkt: pkt.length - 6),
    ]

    @property
    def is_compressed(self) -> bool:
        return bool(self.raw_msg_type & COMPRESSION_FLAG)

    @property
    def msg_type(self) -> MessageType | int:
        _msg_type = self.raw_msg_type & MESSAGE_TYPE_MASK
        try:
            return MessageType(_msg_type)
        except ValueError:
            return _msg_type

    @classmethod
    def tcp_reassemble(cls, data: bytes, metadata, session) -> None | GamePacket:
        if len(data) < 4:
            return None
        total_len = struct.unpack("!I", data[:4])[0]
        if total_len < 6 or total_len > MAX_PACKET_SIZE:
            return None
        if len(data) < total_len:
            return None
        return cls(data[:total_len])

    def extract_padding(self, data):
        length = len(data)
        if length < 4:
            return None, data
        expected_length = struct.unpack("!I", data[:4])[0]
        if length > expected_length:
            return data[:expected_length], data[expected_length:]
        elif length < expected_length:
            return None, data
        return data, None


original_guess_payload_class = TCP.guess_payload_class


def tcp_guess_payload_class(tcp_packet, payload):
    payload = bytes(payload)
    if len(payload) < 4:
        return original_guess_payload_class(tcp_packet, payload)

    try:
        expected_length = struct.unpack("!I", payload[:4])[0]
    except struct.error:
        return original_guess_payload_class(tcp_packet, payload)

    if expected_length < 6 or expected_length > MAX_PACKET_SIZE:
        return original_guess_payload_class(tcp_packet, payload)

    if len(payload) < expected_length:
        return original_guess_payload_class(tcp_packet, payload)

    if is_payload_game_packet(payload):
        return GamePacket

    if len(payload) >= 6:
        raw_msg_type = struct.unpack("!H", payload[4:6])[0]
        if raw_msg_type & ~0xFFFF:
            return original_guess_payload_class(tcp_packet, payload)

        msg_type_val = raw_msg_type & MESSAGE_TYPE_MASK
        try:
            MessageType(msg_type_val)
        except ValueError:
            return original_guess_payload_class(tcp_packet, payload)

    if len(payload) >= expected_length:
        return GamePacket
    return original_guess_payload_class(tcp_packet, payload)


TCP.guess_payload_class = tcp_guess_payload_class


__all__ = ["GamePacket"]
