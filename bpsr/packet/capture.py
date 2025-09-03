from __future__ import annotations

from scapy.all import IP, TCP, sniff
from scapy.sessions import TCPSession

from bpsr.parser import parse_packet

# Import handlers to register them
from ..handler import general, handle_message, notify_handler  # noqa: F401
from ..logutil import get_logger
from ..utils import hex_preview
from .capture_utils import get_local_ip
from .game_packet import GamePacket
from .interface import get_interface_description


class PacketCapture:
    def __init__(self):
        self.client_ip = get_local_ip()
        # self.filter = f"host {self.client_ip} and tcp and not port 53"
        self.filter = "tcp and not port 53"
        self.interface: str | None = None
        self.logger = get_logger("PacketCapture")
        self.tcp_session = TCPSession()

    def run(self):
        if self.interface:
            description = get_interface_description(self.interface)
            interface_info = f" on interface: {description}"
        else:
            interface_info = " (default interface)"

        self.logger.info(f"Starting packet capture with filter: {self.filter}{interface_info}")
        sniff(filter=self.filter, prn=self._handle_packet, iface=self.interface, session=self.tcp_session)

    def stop(self):
        # TODO
        pass

    def set_interface(self, interface: str | None):
        self.interface = interface

    def _log_fallback_packet(self, game_pkt: GamePacket, ip, tcp) -> None:
        self.logger.info(f"PDU {ip.src}:{tcp.sport}->{ip.dst}:{tcp.dport} " f"len={game_pkt.length} data={hex_preview(game_pkt.raw_data)}")

    def _handle_packet(self, pkt):
        if GamePacket not in pkt:
            return

        ip = pkt[IP]
        game_pkt = pkt[GamePacket]

        try:
            message = parse_packet(game_pkt, ip.src == self.client_ip)
            handle_message(message)
        except Exception as e:
            self.logger.error(f"Packet processing failed: {e}")
            self._log_fallback_packet(game_pkt, ip, pkt[TCP])


__all__ = ["PacketCapture"]
