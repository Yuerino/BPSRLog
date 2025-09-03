from __future__ import annotations

import sys
from typing import NamedTuple

from scapy.arch import get_if_list
from scapy.config import conf


class NetworkInterface(NamedTuple):
    index: int
    name: str
    description: str
    address: str | None


def get_default_interface() -> str | None:
    return conf.iface


def list_interfaces() -> list[NetworkInterface]:
    interfaces = []
    interface_names = get_if_list()

    for i, name in enumerate(interface_names):
        description = name
        address = None

        if sys.platform == "win32" and hasattr(conf, "ifaces"):
            try:
                iface_obj = conf.ifaces.get(name)
                if iface_obj:
                    if hasattr(iface_obj, "description") and iface_obj.description:
                        description = iface_obj.description
                    if hasattr(iface_obj, "ip") and iface_obj.ip:
                        address = iface_obj.ip
            except (AttributeError, KeyError):
                pass

        interfaces.append(NetworkInterface(index=i + 1, name=name, description=description, address=address))

    return interfaces


def print_interfaces(interfaces: list[NetworkInterface]) -> None:
    print("\nAvailable network interfaces:")
    print("-" * 80)
    print(f"{'#':<3} {'Name':<25} {'Address':<15} {'Description'}")
    print("-" * 80)

    for iface in interfaces:
        address_str = iface.address or "N/A"
        print(f"{iface.index:<3} {iface.name:<25} {address_str:<15} {iface.description}")
    print("-" * 80)


def select_interface_interactive() -> str | None:
    interfaces = list_interfaces()

    if not interfaces:
        print("No network interfaces found.")
        return None

    print_interfaces(interfaces)

    while True:
        try:
            choice = input(f"\nSelect interface (1-{len(interfaces)}, or 'q' to quit): ").strip()

            if choice.lower() == "q":
                return None

            index = int(choice)
            if 1 <= index <= len(interfaces):
                selected = interfaces[index - 1]
                print(f"Selected: {selected.name} ({selected.description})")
                return selected.name
            else:
                print(f"Please enter a number between 1 and {len(interfaces)}")

        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return None


def resolve_interface(interface_spec: str | None) -> str | None:
    if interface_spec is None:
        return get_default_interface()

    interfaces = list_interfaces()

    # Try to match by exact name first
    for iface in interfaces:
        if iface.name == interface_spec:
            return iface.name

    # Try to match by index
    try:
        index = int(interface_spec)
        for iface in interfaces:
            if iface.index == index:
                return iface.name
    except ValueError:
        pass

    return None


def get_interface_description(interface_name: str) -> str:
    try:
        iface_obj = conf.ifaces.get(interface_name)
        if iface_obj:
            if hasattr(iface_obj, "description"):
                return iface_obj.description
    except (AttributeError, KeyError):
        pass
    return interface_name


__all__ = ["NetworkInterface", "get_default_interface", "get_interface_description", "list_interfaces", "print_interfaces", "select_interface_interactive", "resolve_interface"]
