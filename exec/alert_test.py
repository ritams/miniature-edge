from __future__ import annotations
import os
import logging
from dotenv import load_dotenv

from common.logging import setup_logging
from alerts.telegram import send as tg_send


def main() -> None:
    load_dotenv()
    setup_logging()
    LOG = logging.getLogger(__name__)
    text = os.getenv("ALERT_TEST_TEXT", "Miniature-Edge alert test ✅")
    try:
        tg_send(text)
        LOG.info("alert test sent")
    except Exception as e:
        LOG.exception("alert test failed: %s", e)


if __name__ == "__main__":
    main()
