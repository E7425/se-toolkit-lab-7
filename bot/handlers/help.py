"""Handler for /help command."""


def handle_help() -> str:
    """Handle /help command.

    Returns:
        List of available commands with descriptions.
    """
    return (
        "📚 LMS Bot - Help\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/health - Check backend status\n"
        "/labs - List all available labs\n"
        "/scores <lab_id> - Get score distribution for a lab\n\n"
        "Examples:\n"
        "/scores lab-01\n"
        "/scores lab-07\n\n"
        "Natural language queries also work:\n"
        "• What labs are available?\n"
        "• Show my scores for lab 4\n"
        "• How am I doing?"
    )
