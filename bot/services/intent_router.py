"""Intent router with LLM tool calling."""

import asyncio
import json
import sys
from typing import Any

from config import settings
from services.lms_api import LMSAPIClient, LMSAPIError
from services.llm_api import LLMAPIClient, get_tool_definitions


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------


SYSTEM_PROMPT = """You are an AI assistant for a Learning Management System (LMS). 
You have access to backend API tools to fetch data about labs, students, scores, and analytics.

Your job is to:
1. Understand the user's question about their learning progress
2. Call the appropriate tools to fetch relevant data
3. Analyze the data and provide a clear, helpful answer

Tool calling rules:
- Always call tools to get real data before answering
- If you need data from multiple labs, call tools for each lab
- After receiving tool results, analyze them and provide a summary
- If the user asks about "worst" or "best", compare the data
- If you don't have enough information, ask clarifying questions

Available tools:
- get_items: Get list of all labs and tasks
- get_learners: Get enrolled students and groups
- get_scores: Get score distribution for a lab (4 buckets)
- get_pass_rates: Get per-task pass rates for a lab
- get_timeline: Get submission timeline for a lab
- get_groups: Get per-group performance for a lab
- get_top_learners: Get top N learners for a lab
- get_completion_rate: Get completion rate for a lab
- trigger_sync: Refresh data from autochecker

When answering:
- Be specific with numbers (e.g., "71.4%" not "about 70%")
- Mention attempt counts when relevant
- Compare values when asked about "best" or "worst"
- Keep responses concise but informative
"""


# ---------------------------------------------------------------------------
# Intent Router
# ---------------------------------------------------------------------------


class IntentRouter:
    """Routes user queries to backend API via LLM tool calling."""

    def __init__(self):
        """Initialize the intent router."""
        if not settings.lms_api_base_url or not settings.lms_api_key:
            raise ValueError("LMS API configuration missing")
        if not settings.llm_api_base_url or not settings.llm_api_key:
            raise ValueError("LLM API configuration missing")

        self.lms_client = LMSAPIClient(
            base_url=settings.lms_api_base_url,
            api_key=settings.lms_api_key,
        )
        self.llm_client = LLMAPIClient(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_api_model,
        )
        self.tools = get_tool_definitions()

    async def route(self, user_message: str) -> str:
        """Route a user message through LLM tool calling.

        Args:
            user_message: Raw user input.

        Returns:
            Formatted response text.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            response = await self.llm_client.chat(messages, tools=self.tools)

            # Check for LLM errors
            if "error" in response:
                return f"LLM error: {response['error']}"

            # Extract tool calls
            tool_calls = self.llm_client.extract_tool_calls(response)

            if not tool_calls:
                # No tool calls - LLM has final answer
                return self.llm_client.get_response_text(response)

            # Execute tool calls
            tool_results = []
            for tc in tool_calls:
                print(
                    f"[tool] LLM called: {tc['name']}({tc['arguments']})",
                    file=sys.stderr,
                    flush=True,
                )
                result = await self._execute_tool(tc["name"], tc["arguments"])
                tool_results.append(
                    {
                        "tool_call_id": tc["id"],
                        "name": tc["name"],
                        "result": result,
                    }
                )
                print(
                    f"[tool] Result: {self._truncate_result(result)}",
                    file=sys.stderr,
                    flush=True,
                )

            # Feed tool results back to LLM
            print(
                f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM",
                file=sys.stderr,
                flush=True,
            )

            # Add tool results to messages
            for tr in tool_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "name": tr["name"],
                        "content": json.dumps(tr["result"], ensure_ascii=False),
                    }
                )

        return "Unable to process request after multiple attempts."

    async def _execute_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool by name.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool result.
        """
        try:
            if name == "get_items":
                return await self.lms_client.get_labs()
            elif name == "get_learners":
                return await self.lms_client.get_learners()
            elif name == "get_scores":
                return await self.lms_client.get_scores(arguments.get("lab", ""))
            elif name == "get_pass_rates":
                return await self.lms_client.get_pass_rates(arguments.get("lab", ""))
            elif name == "get_timeline":
                return await self.lms_client.get_timeline(arguments.get("lab", ""))
            elif name == "get_groups":
                return await self.lms_client.get_groups(arguments.get("lab", ""))
            elif name == "get_top_learners":
                return await self.lms_client.get_top_learners(
                    arguments.get("lab", ""), arguments.get("limit", 5)
                )
            elif name == "get_completion_rate":
                return await self.lms_client.get_completion_rate(
                    arguments.get("lab", "")
                )
            elif name == "trigger_sync":
                return await self.lms_client.trigger_sync()
            else:
                return {"error": f"Unknown tool: {name}"}
        except LMSAPIError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)}"}

    def _truncate_result(self, result: Any, max_length: int = 100) -> str:
        """Truncate result for debug output.

        Args:
            result: Tool result.
            max_length: Maximum length.

        Returns:
            Truncated string.
        """
        if isinstance(result, list):
            s = f"{len(result)} items"
        elif isinstance(result, dict):
            s = f"{len(result)} keys"
        else:
            s = str(result)[:max_length]
        return s
