from __future__ import annotations

import io
import subprocess
import sys

import zstandard as zstd

_decompressor: zstd.ZstdDecompressor | None = None


def hex_preview(data: bytes, limit: int = 64) -> str:
    h = data[:limit].hex()
    if len(data) > limit:
        return f"{h}...(+{len(data) - limit}b)"
    return h


def decompress_zstd(data: bytes) -> bytes | None:
    global _decompressor  # noqa: PLW0603

    if not _decompressor:
        _decompressor = zstd.ZstdDecompressor()

    with _decompressor.stream_reader(io.BytesIO(data)) as reader:
        return reader.read()


VPN_INTERFACE_PREFIXES = ("tun", "tap", "ppp", "vpn", "wg", "openvpn")


def detect_vpn() -> bool:
    if sys.platform == "win32":
        result = subprocess.run(["ipconfig"], check=False, capture_output=True, text=True, timeout=5)
        interfaces = result.stdout.lower()
    for prefix in VPN_INTERFACE_PREFIXES:
        if prefix in interfaces:
            return True

    return False


class ParseError(Exception):
    metadata = {}

    def __init__(self, message: str, payload: bytes | None, metadata: dict | None = None):
        super().__init__(message)
        if payload is not None:
            self.metadata["preview"] = hex_preview(payload)
        if metadata is not None:
            self.metadata.update(metadata)


__all__ = ["hex_preview", "decompress_zstd", "detect_vpn", "ParseError"]
