from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

_LOGGER: logging.Logger | None = None

DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "asctime"):
            record.asctime = datetime.fromtimestamp(record.created, tz=UTC).strftime(DEFAULT_DATEFMT)
        return super().format(record)


def get_logger(name: str = "bpsr") -> logging.Logger:
    global _LOGGER  # noqa: PLW0603
    if _LOGGER is None:
        logger = logging.getLogger("bpsr")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(PlainFormatter(DEFAULT_FORMAT, DEFAULT_DATEFMT))
        logger.addHandler(handler)
        logger.propagate = False
        _LOGGER = logger
    return _LOGGER if name == "bpsr" else _LOGGER.getChild(name)


def configure(verbose: bool = False):
    logger = get_logger()
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    logfile = f"logs/{ts}.log"

    path = Path(logfile)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(PlainFormatter(DEFAULT_FORMAT, DEFAULT_DATEFMT))
    logger.addHandler(fh)


__all__ = ["get_logger", "configure"]
