from __future__ import annotations

import io
import socket
import struct

from bpsr.parser.constants import ServiceID

WORLD_NTF_SERVICE_ID = ServiceID.WORLD_NTF.to_bytes(8, byteorder="big")


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def is_payload_game_packet(buf: bytes) -> bool:
    if len(buf) <= 10:
        return False
    data = buf[10:]
    reader = io.BytesIO(data)

    while True:
        remaining = len(reader.getbuffer()) - reader.tell()
        if remaining < 4:
            break
        length_bytes = reader.read(4)
        if len(length_bytes) < 4:
            break
        msg_len = struct.unpack(">I", length_bytes)[0]
        remaining = len(reader.getbuffer()) - reader.tell()
        if remaining < msg_len - 4:
            break
        msg_data = reader.read(msg_len - 4)
        if len(msg_data) < msg_len - 4:
            break
        # skip 2 bytes for message type
        if len(msg_data) >= 2 + len(WORLD_NTF_SERVICE_ID):
            actual_sig = msg_data[2 : 2 + len(WORLD_NTF_SERVICE_ID)]
            if actual_sig == WORLD_NTF_SERVICE_ID:
                return True
    return False


__all__ = ["get_local_ip", "is_payload_game_packet"]
