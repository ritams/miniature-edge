from __future__ import annotations
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure a concise, structured-ish logger.

    - Avoid duplicate handlers on re-run.
    - Format: time level module: message
    """
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%SZ"
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root.addHandler(handler)
