# Telegram Bot Development Plan

## Overview

This document describes the development plan for the LMS Telegram Bot that integrates with the Learning Management Service API and provides students with access to their lab progress, scores, and AI-powered assistance.

## Architecture Principles

### Testable Handler Architecture (P0.1)

The core design principle is **separation of concerns**: command handlers are pure functions that don't know about Telegram. They receive simple input (strings, parsed arguments) and return text responses. This enables:

- **Offline testing** via `--test` mode without Telegram connection
- **Unit testing** with pytest without mocking Telegram
- **Reusability** - same handlers work for CLI, Telegram, or future web interface

```
User Input → Router → Handler (pure function) → Response
                ↑
         (Telegram CLI test)
```

### Project Structure

```
bot/
├── bot.py              # Entry point: Telegram startup + --test mode
├── config.py           # Environment configuration
├── handlers/           # Command handlers (no Telegram dependency)
│   ├── __init__.py
│   ├── start.py        # /start command
│   ├── help.py         # /help command
│   ├── health.py       # /health command
│   ├── scores.py       # /scores command
│   └── labs.py         # /labs command
├── services/           # External API clients
│   ├── __init__.py
│   ├── lms_api.py      # LMS API client
│   └── llm_api.py      # LLM API client
├── pyproject.toml      # Dependencies
└── PLAN.md             # This file
```

## Development Tasks

### Task 1: Project Scaffold (Current)

Create the basic structure with:
- Entry point (`bot.py`) with `--test` mode support
- Empty handler modules returning placeholder text
- Configuration loader reading from `.env.bot.secret`
- Dependencies in `pyproject.toml`

**Acceptance Criteria:**
- `uv run bot.py --test "/start"` prints welcome message
- Exit code 0, no tracebacks
- No Telegram connection required

### Task 2: Handler Implementation

Implement real handlers for each command:

| Command | Description | Input | Output |
|---------|-------------|-------|--------|
| `/start` | Welcome message | - | Welcome text with available commands |
| `/help` | Command list | - | List of commands with descriptions |
| `/health` | Backend status | - | "OK" or error message |
| `/scores <lab>` | Lab scores | lab ID (e.g., "lab-04") | Score distribution chart/data |
| `/labs` | Available labs | - | List of labs with progress |

### Task 3: LMS API Integration

Create `services/lms_api.py`:
- HTTP client with authentication (API key)
- Methods: `get_health()`, `get_scores(lab_id)`, `get_labs()`
- Error handling with retries
- Timeout configuration

### Task 4: Intent Routing (LLM Integration)

For natural language queries like "what labs are available":
- Create `services/llm_api.py` for LLM integration
- Implement intent classification
- Route to appropriate handler based on intent

### Task 5: Deployment

- Docker container for the bot
- Health check endpoint
- Graceful shutdown handling
- Logging configuration

## Testing Strategy

### Test Mode (`--test`)

```bash
cd bot
uv run bot.py --test "/start"
uv run bot.py --test "/help"
uv run bot.py --test "/health"
uv run bot.py --test "/scores lab-04"
uv run bot.py --test "what labs are available"
```

### Unit Tests (Future)

```bash
cd bot
uv run pytest tests/
```

## Deployment Checklist

1. Create `.env.bot.secret` on VM with real values
2. `cd bot && uv sync`
3. Start bot: `nohup uv run bot.py > bot.log 2>&1 &`
4. Verify in Telegram: send `/start`
5. Check logs: `tail -20 bot.log`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token | Yes (production) |
| `LMS_API_BASE_URL` | LMS API base URL | Yes |
| `LMS_API_KEY` | LMS API authentication key | Yes |
| `LLM_API_BASE_URL` | LLM API endpoint | Yes (for Task 4) |
| `LLM_API_KEY` | LLM API authentication key | Yes (for Task 4) |
| `LLM_API_MODEL` | Model name for LLM | No (default: coder-model) |

## Error Handling

- API timeouts: retry with exponential backoff
- API errors: return user-friendly message
- Unknown commands: suggest `/help`
- Test mode: print errors to stderr, exit code 1

## Future Enhancements

- Inline keyboards for lab selection
- Progress notifications
- Group leaderboard
- Multi-language support (i18n)
