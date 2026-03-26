#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Usage:
    uv run bot.py                  # Start Telegram bot
    uv run bot.py --test "/start"  # Test mode (no Telegram connection)
"""

import argparse
import asyncio
import sys
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart

from config import settings
from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)
from services import LMSAPIClient, LLMAPIClient, LMSAPIError
from services.intent_router import IntentRouter


# ---------------------------------------------------------------------------
# Helper Messages
# ---------------------------------------------------------------------------


def get_unknown_command_message(command: str) -> str:
    """Return a helpful message for unknown commands.

    Args:
        command: The unknown command string.

    Returns:
        Helpful message suggesting available commands.
    """
    return (
        f"❓ Unknown command: {command}\n\n"
        "I didn't understand that. Here are the available commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show all available commands\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab_id> - Get scores for a lab (e.g., /scores lab-04)\n\n"
        "You can also ask in natural language:\n"
        "• What labs are available?\n"
        "• Show my scores for lab 4"
    )


# ---------------------------------------------------------------------------
# Test Mode
# ---------------------------------------------------------------------------


def parse_command(command: str) -> tuple[str, str]:
    """Parse a command string into command name and arguments.

    Args:
        command: Command string (e.g., "/scores lab-04" or "/start").

    Returns:
        Tuple of (command_name, arguments).
    """
    parts = command.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    cmd = parts[0].lstrip("/")
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


def get_handler_for_command(cmd: str):
    """Get the handler function for a command.

    Args:
        cmd: Command name (without /).

    Returns:
        Handler function or None if not found.
    """
    handlers = {
        "start": handle_start,
        "help": handle_help,
        "health": handle_health,
        "labs": handle_labs,
        "scores": handle_scores,
    }
    return handlers.get(cmd)


def run_test_mode(command: str) -> int:
    """Run a command in test mode.

    Args:
        command: Command string to test.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Handle empty command
    if not command or not command.strip():
        print(get_unknown_command_message("(empty)"))
        return 0

    cmd, args = parse_command(command)

    # Check if it's a slash command
    if command.startswith("/"):
        if not cmd:
            print(get_unknown_command_message(command))
            return 0

        handler = get_handler_for_command(cmd)

        if handler:
            # Known slash command - use handler
            if args or cmd == "scores":
                result = handler(args)
            else:
                result = handler()
            print(result)
            return 0

    # Not a known slash command - try LLM intent router
    if settings.llm_api_base_url and settings.llm_api_key and settings.lms_api_base_url and settings.lms_api_key:
        try:
            router = IntentRouter()

            async def route_query():
                result = await router.route(command)
                # Check if it's an LLM connection error
                if result.startswith("LLM error:"):
                    # Fallback: suggest using slash commands
                    print(f"⚠️ LLM service unavailable. Please use slash commands:\n\n/help - Show available commands\n/labs - List labs\n/scores lab-04 - Get scores")
                    return 0
                print(result)
                return 0

            return asyncio.run(route_query())
        except ValueError as e:
            # Configuration error
            print(f"Configuration error: {e}", file=sys.stderr)
            print(get_unknown_command_message(command))
            return 0
        except Exception as e:
            print(f"LLM router error: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"⚠️ LLM service unavailable. Please use slash commands:\n\n/help - Show available commands\n/labs - List labs\n/scores lab-04 - Get scores")
            return 0

    # No LLM configured - return helpful message
    print(get_unknown_command_message(command))
    return 0


# ---------------------------------------------------------------------------
# Telegram Bot Mode
# ---------------------------------------------------------------------------


async def cmd_start(message: types.Message):
    """Handle /start command."""
    await message.answer(handle_start())


async def cmd_help(message: types.Message):
    """Handle /help command."""
    await message.answer(handle_help())


async def cmd_health(message: types.Message):
    """Handle /health command."""
    if not settings.lms_api_base_url or not settings.lms_api_key:
        await message.answer(
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )
        return

    lms_client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    try:
        result = await lms_client.health_check()
        status = f"🟢 Backend is healthy. {result['item_count']} items available."
        await message.answer(status)
    except LMSAPIError as e:
        await message.answer(f"🔴 Backend error: {e.message}")


async def cmd_labs(message: types.Message):
    """Handle /labs command."""
    if not settings.lms_api_base_url or not settings.lms_api_key:
        await message.answer(
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )
        return

    lms_client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    try:
        labs = await lms_client.get_labs()
        if not labs:
            await message.answer("📋 No labs available.\n\nThe backend may not have any labs yet.")
            return

        lines = ["📚 Available labs:"]
        for lab in labs:
            title = lab.get("title", "Unknown")
            lines.append(f"• {title}")

        await message.answer("\n".join(lines))
    except LMSAPIError as e:
        await message.answer(f"🔴 Backend error: {e.message}")


async def cmd_scores(message: types.Message):
    """Handle /scores command."""
    if not settings.lms_api_base_url or not settings.lms_api_key:
        await message.answer(
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )
        return

    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    if not args or not args.strip():
        await message.answer(
            "❌ Please specify a lab ID.\n\n"
            "Usage: /scores <lab_id>\n"
            "Example: /scores lab-04"
        )
        return

    lab_id = args.strip()
    lms_client = LMSAPIClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )

    try:
        pass_rates = await lms_client.get_pass_rates(lab_id)
        if not pass_rates:
            await message.answer(f"📊 No pass rate data available for {lab_id}.")
            return

        lines = [f"📈 Pass rates for {lab_id}:"]
        for item in pass_rates:
            task_title = item.get("task", "Unknown task")
            pass_rate = item.get("pass_rate", 0)
            attempts = item.get("attempts", 0)
            lines.append(f"• {task_title}: {pass_rate:.1f}% ({attempts} attempts)")

        await message.answer("\n".join(lines))
    except LMSAPIError as e:
        await message.answer(f"🔴 Backend error: {e.message}")


async def handle_message(message: types.Message):
    """Handle natural language messages with LLM tool calling."""
    if not settings.llm_api_base_url or not settings.llm_api_key:
        # No LLM configured - respond with helpful message for unknown inputs
        await message.answer(
            "🤔 I'm not sure what you mean. Try one of these commands:\n\n"
            "/start - Welcome message\n"
            "/help - Show all available commands\n"
            "/health - Check backend status\n"
            "/labs - List available labs\n"
            "/scores <lab_id> - Get scores for a lab"
        )
        return

    if not settings.lms_api_base_url or not settings.lms_api_key:
        await message.answer(
            "⚠️ LMS API configuration missing.\n\n"
            "Please set LMS_API_BASE_URL and LMS_API_KEY in .env.bot.secret"
        )
        return

    try:
        router = IntentRouter()
        result = await router.route(message.text)
        await message.answer(result)
    except ValueError as e:
        await message.answer(f"Configuration error: {e}")
    except Exception as e:
        await message.answer(f"🤔 I encountered an error: {type(e).__name__}. Please try again or use /help for available commands.")


def run_telegram_mode() -> None:
    """Start the Telegram bot."""
    if not settings.bot_token:
        print("Error: BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Register handlers
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_health, Command("health"))
    dp.message.register(cmd_labs, Command("labs"))
    dp.message.register(cmd_scores, Command("scores"))
    dp.message.register(handle_message)

    # Start polling
    asyncio.run(dp.start_polling(bot))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        metavar="COMMAND",
        help="Test mode: run a command without Telegram connection",
    )

    args = parser.parse_args()

    if args.test:
        return run_test_mode(args.test)

    run_telegram_mode()
    return 0


if __name__ == "__main__":
    sys.exit(main())
