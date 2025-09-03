from __future__ import annotations

import argparse
import sys

from bpsr.config import Config, get_default_config_path

from .logutil import configure, get_logger
from .packet import PacketCapture, get_default_interface, list_interfaces, print_interfaces, resolve_interface, select_interface_interactive


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bpsr", description="Blue Protocol Logger")
    p.add_argument("--iface", help="Interface name or index (default: auto-detect)")
    p.add_argument("-m", "--manual", action="store_true", help="Manually select network interface")
    p.add_argument("--list-ifaces", action="store_true", help="List available interfaces and exit")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    return p


def handle_interface_selection(args) -> str | None:
    logger = get_logger("interface")

    if args.list_ifaces:
        print_interfaces(list_interfaces())
        sys.exit(0)

    if args.manual:
        interface = select_interface_interactive()
        if interface is None:
            logger.error("No interface selected. Exiting.")
            sys.exit(1)
        return interface

    if args.iface:
        interface = resolve_interface(args.iface)
        if interface is None:
            logger.error(f"Interface '{args.iface}' not found.")
            sys.exit(1)
        return interface

    default_interface = get_default_interface()
    if not default_interface:
        logger.error("No default interface detected")
        sys.exit(1)

    return default_interface


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    configure(args.verbose)

    interface = handle_interface_selection(args)
    logger = get_logger("main")

    config = Config.load_from_file(get_default_config_path())

    discord_client = None
    if config.discord.enabled:
        from .discord import DiscordWebSocketClient
        from .handler.notify_handler import set_discord_client

        discord_client = DiscordWebSocketClient(config.discord)
        set_discord_client(discord_client)
        discord_client.start()
        logger.info("Discord WebSocket client initialized and started")

    packet_capture = PacketCapture()
    packet_capture.set_interface(interface)

    try:
        capture_background = False
        if capture_background:
            packet_capture.run_threaded()

            try:
                while packet_capture.running:
                    import time

                    time.sleep(1.0)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
        else:
            packet_capture.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        if packet_capture.running:
            packet_capture.stop()

        if discord_client:
            discord_client.stop()

        config.save_to_file(get_default_config_path())

        logger.info("Shutdown complete")


if __name__ == "__main__":  # pragma: no cover
    main()
