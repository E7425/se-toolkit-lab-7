"""Command handlers for the Telegram bot.

Handlers are pure functions that take input and return text.
They don't know about Telegram - this enables test mode.
"""

from .start import handle_start
from .help import handle_help
from .health import handle_health
from .labs import handle_labs
from .scores import handle_scores

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
]
