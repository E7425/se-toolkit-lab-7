"""Handler for /start command."""


def handle_start() -> str:
    """Handle /start command.

    Returns:
        Welcome message with available commands.
    """
    return (
        "👋 Welcome to the LMS Bot!\n\n"
        "I can help you track your lab progress and scores.\n\n"
        "Available commands:\n"
        "/help - Show this help message\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get scores for a specific lab\n\n"
        "You can also ask me questions in natural language!"
    )
