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
from services import LMSAPIClient, LLMAPIClient


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
    cmd, args = parse_command(command)

    if not cmd:
        print("Error: Empty command", file=sys.stderr)
        return 1

    handler = get_handler_for_command(cmd)

    if handler is None:
        # Try LLM intent classification for natural language queries
        if settings.llm_api_base_url and settings.llm_api_key:
            llm_client = LLMAPIClient(
                base_url=settings.llm_api_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_api_model,
            )

            async def classify_and_handle():
                intent = await llm_client.classify_intent(command)
                handler = get_handler_for_command(intent)
                if handler:
                    if args or intent == "scores":
                        result = handler(args if args else "")
                    else:
                        result = handler()
                    print(result)
                    return 0
                print(f"Unknown command: {command}", file=sys.stderr)
                return 1

            return asyncio.run(classify_and_handle())

        print(f"Unknown command: {command}", file=sys.stderr)
        return 1

    # Call handler
    if args or cmd == "scores":
        result = handler(args)
    else:
        result = handler()

    print(result)
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
    # Real health check with LMS API
    if settings.lms_api_base_url and settings.lms_api_key:
        lms_client = LMSAPIClient(
            base_url=settings.lms_api_base_url,
            api_key=settings.lms_api_key,
        )
        is_healthy = await lms_client.health_check()
        status = "🟢 OK" if is_healthy else "🔴 Unavailable"
        await message.answer(f"Backend status: {status}")
    else:
        await message.answer(handle_health())


async def cmd_labs(message: types.Message):
    """Handle /labs command."""
    await message.answer(handle_labs())


async def cmd_scores(message: types.Message):
    """Handle /scores command."""
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    await message.answer(handle_scores(args))


async def handle_message(message: types.Message):
    """Handle natural language messages with LLM intent classification."""
    if not settings.llm_api_base_url or not settings.llm_api_key:
        return

    llm_client = LLMAPIClient(
        base_url=settings.llm_api_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_api_model,
    )

    intent = await llm_client.classify_intent(message.text)
    handler = get_handler_for_command(intent)

    if handler:
        if intent == "scores":
            args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
            await message.answer(handler(args))
        else:
            await message.answer(handler())


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
