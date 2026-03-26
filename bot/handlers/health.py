"""Handler for /health command."""

import asyncio

from config import settings
from services.lms_api import LMSAPIClient, LMSAPIError


def handle_health() -> str:
    """Handle /health command.

    Returns:
        Backend health status with item count or error message.
    """
    if not settings.lms_api_base_url or not settings.lms_api_key:
        return (
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )

    client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    async def fetch_health():
        try:
            result = await client.health_check()
            return (
                f"🟢 Backend is healthy. "
                f"{result['item_count']} items available."
            )
        except LMSAPIError as e:
            return f"🔴 Backend error: {e.message}"

    return asyncio.run(fetch_health())
