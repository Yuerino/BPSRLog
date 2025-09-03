from __future__ import annotations


def main(*args, **kwargs):
    from .__main__ import main as _main  # noqa: PLC0415

    return _main(*args, **kwargs)


__all__ = ["main"]
