from __future__ import annotations
import logging
import sys
import time


def setup_logging(level: int = logging.INFO) -> None:
    """Configure a concise UTC logger.

    - Avoid duplicate handlers on re-run.
    - Format: time level module: message (ISO8601 with Z)
    """
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%SZ"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    # Ensure UTC timestamps for the 'Z' suffix
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)

    root.addHandler(handler)
