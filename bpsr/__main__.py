from __future__ import annotations

import argparse
import sys

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

    packet_capture = PacketCapture()
    packet_capture.set_interface(interface)
    packet_capture.run()


if __name__ == "__main__":  # pragma: no cover
    main()
