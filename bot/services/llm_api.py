"""LLM API client for intent recognition and natural language responses."""

import httpx


class LLMAPIClient:
    """Client for the LLM API."""

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

    async def chat(self, messages: list[dict]) -> str:
        """Send a chat request to the LLM.

        Args:
            messages: List of message objects with 'role' and 'content'.

        Returns:
            LLM response text.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            except httpx.HTTPError:
                return ""

    async def classify_intent(self, user_input: str) -> str:
        """Classify user intent to route to appropriate handler.

        Args:
            user_input: Raw user message.

        Returns:
            Intent name (e.g., "scores", "labs", "help", "unknown").
        """
        system_prompt = (
            "You are an intent classifier for an LMS Telegram bot. "
            "Classify the user's message into one of these intents: "
            "start, help, health, labs, scores, unknown. "
            "Respond with ONLY the intent name."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = await self.chat(messages)
        intent = response.strip().lower()

        # Validate intent
        valid_intents = {"start", "help", "health", "labs", "scores"}
        if intent in valid_intents:
            return intent

        # Check for lab-specific queries
        if "score" in user_input.lower() or "grade" in user_input.lower():
            return "scores"
        if "lab" in user_input.lower():
            return "labs"

        return "unknown"
