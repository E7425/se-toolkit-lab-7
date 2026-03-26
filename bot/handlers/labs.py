"""Handler for /labs command."""

import asyncio

from config import settings
from services.lms_api import LMSAPIClient, LMSAPIError


def handle_labs() -> str:
    """Handle /labs command.

    Returns:
        List of available labs with titles or error message.
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

    async def fetch_labs():
        try:
            labs = await client.get_labs()
            if not labs:
                return "📋 No labs available.\n\nThe backend may not have any labs yet."

            lines = ["📚 Available labs:"]
            for lab in labs:
                title = lab.get("title", "Unknown")
                lines.append(f"• {title}")

            return "\n".join(lines)
        except LMSAPIError as e:
            return f"🔴 Backend error: {e.message}"

    return asyncio.run(fetch_labs())
