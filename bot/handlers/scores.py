"""Handler for /scores command."""

import asyncio

from config import settings
from services.lms_api import LMSAPIClient, LMSAPIError


def handle_scores(args: str = "") -> str:
    """Handle /scores command.

    Args:
        args: Lab ID (e.g., "lab-04") or empty string.

    Returns:
        Pass rates for the specified lab or error message.
    """
    if not args or not args.strip():
        return (
            "❌ Please specify a lab ID.\n\n"
            "Usage: /scores <lab_id>\n"
            "Example: /scores lab-04"
        )

    if not settings.lms_api_base_url or not settings.lms_api_key:
        return (
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )

    lab_id = args.strip()
    client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    async def fetch_scores():
        try:
            pass_rates = await client.get_pass_rates(lab_id)
            if not pass_rates:
                return f"📊 No pass rate data available for {lab_id}."

            # Format: "Lab Name — XX.X% (N attempts)"
            lines = [f"📈 Pass rates for {lab_id}:"]
            for item in pass_rates:
                task_title = item.get("task", "Unknown task")
                pass_rate = item.get("pass_rate", 0)
                attempts = item.get("attempts", 0)
                lines.append(f"• {task_title}: {pass_rate:.1f}% ({attempts} attempts)")

            return "\n".join(lines)
        except LMSAPIError as e:
            return f"🔴 Backend error: {e.message}"

    return asyncio.run(fetch_scores())
