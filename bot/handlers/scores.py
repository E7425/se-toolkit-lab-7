"""Handler for /scores command."""


def handle_scores(args: str = "") -> str:
    """Handle /scores command.

    Args:
        args: Lab ID (e.g., "lab-04") or empty string.

    Returns:
        Score distribution for the specified lab.
    """
    if not args or not args.strip():
        return (
            "❌ Please specify a lab ID.\n\n"
            "Usage: /scores <lab_id>\n"
            "Example: /scores lab-04"
        )

    lab_id = args.strip()

    # Placeholder - will be implemented with LMS API integration
    return (
        f"📊 Scores for {lab_id} (placeholder)\n\n"
        "Score Distribution:\n"
        "• 90-100: 5 students\n"
        "• 75-89: 12 students\n"
        "• 50-74: 8 students\n"
        "• 0-49: 3 students\n\n"
        "Your progress: Not implemented yet"
    )
