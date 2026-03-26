"""LLM API client with tool calling support."""

import json
import sys
from typing import Any

import httpx


# ---------------------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------------------


def get_tool_definitions() -> list[dict]:
    """Return LLM tool definitions for all backend endpoints."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "Get list of all available labs and tasks. Use this to discover what labs exist.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get list of enrolled students and their groups. Use for queries about students or groups.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution (4 buckets: 0-49, 50-74, 75-89, 90-100) for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average pass rates and attempt counts for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submission timeline (submissions per day) for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group performance (scores and student counts) for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top N learners by score for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of top learners to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get completion rate percentage for a specific lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Trigger ETL sync to refresh data from autochecker API. Use when user asks to update or sync data.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
    ]


# ---------------------------------------------------------------------------
# LLM API Client
# ---------------------------------------------------------------------------


class LLMAPIClient:
    """Client for the LLM API with tool calling support."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0):
        """Initialize LLM API client.

        Args:
            base_url: Base URL of the LLM API.
            api_key: API key for authentication.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.tools = get_tool_definitions()

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        """Send a chat request to the LLM.

        Args:
            messages: List of message objects with 'role' and 'content'.
            tools: Optional list of tool definitions.

        Returns:
            LLM response dict (may contain tool_calls).
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload: dict = {
                    "model": self.model,
                    "messages": messages,
                }
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {
                    "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                }
            except httpx.HTTPError as e:
                return {"error": f"HTTP error: {type(e).__name__}: {str(e)[:200]}"}

    def extract_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from LLM response.

        Args:
            response: LLM response dict.

        Returns:
            List of tool call dicts with 'id', 'name', and 'arguments'.
        """
        choices = response.get("choices", [])
        if not choices:
            return []

        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])

        result = []
        for tc in tool_calls:
            func = tc.get("function", {})
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

            result.append(
                {
                    "id": tc.get("id", "unknown"),
                    "name": func.get("name", "unknown"),
                    "arguments": arguments,
                }
            )

        return result

    def get_response_text(self, response: dict) -> str:
        """Extract text response from LLM.

        Args:
            response: LLM response dict.

        Returns:
            Text content or empty string.
        """
        choices = response.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return message.get("content", "") or ""
