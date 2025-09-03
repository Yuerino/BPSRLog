from __future__ import annotations

import signal
import threading

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
        self.running = False
        self.thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def run(self):
        if self.interface:
            description = get_interface_description(self.interface)
            interface_info = f" on interface: {description}"
        else:
            interface_info = " (default interface)"

        self.logger.info(f"Starting packet capture with filter: {self.filter}{interface_info}")
        self.running = True
        self._stop_event.clear()

        original_sigint = None
        original_sigterm = None
        if threading.current_thread() is threading.main_thread():
            original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
            original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            sniff(filter=self.filter, prn=self._handle_packet, iface=self.interface, session=self.tcp_session, stop_filter=lambda _: self._stop_event.is_set())
        finally:
            if original_sigint is not None:
                signal.signal(signal.SIGINT, original_sigint)
            if original_sigterm is not None:
                signal.signal(signal.SIGTERM, original_sigterm)
            self.running = False

    def run_threaded(self) -> None:
        if self.thread and self.thread.is_alive():
            self.logger.warning("Packet capture is already running")
            return

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.logger.info("Packet capture started in background thread")

    def stop(self):
        if not self.running:
            return

        self.logger.info("Stopping packet capture...")
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                self.logger.warning("Packet capture thread did not stop gracefully")

        self.logger.info("Packet capture stopped")

    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, stopping packet capture...")
        self.stop()

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
