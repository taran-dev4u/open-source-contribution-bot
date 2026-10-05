"""Notification module for mobile push alerts via ntfy."""

from __future__ import annotations

import logging

import httpx

from src.config import config

logger = logging.getLogger(__name__)


def send_push_notification(title: str, message: str, priority: str = "default", tags: list[str] | None = None) -> bool:
    """Send push notification to phone via ntfy.sh."""
    if not config.ntfy_topic:
        logger.info("NTFY_TOPIC not configured; skipping push alert: %s - %s", title, message)
        return False

    url = f"https://ntfy.sh/{config.ntfy_topic}"
    headers = {
        "Title": title,
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = ",".join(tags)

    try:
        response = httpx.post(url, content=message.encode("utf-8"), headers=headers, timeout=10.0)
        response.raise_for_status()
        logger.info("Successfully dispatched push notification: %s", title)
        return True
    except Exception as exc:
        logger.warning("Failed to send push notification via ntfy: %s", exc)
        return False
