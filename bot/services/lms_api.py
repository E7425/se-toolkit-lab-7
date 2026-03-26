"""LMS API client."""

import httpx


class LMSAPIClient:
    """Client for the Learning Management Service API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        """Initialize LMS API client.

        Args:
            base_url: Base URL of the LMS API.
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def health_check(self) -> bool:
        """Check if the backend is healthy.

        Returns:
            True if backend is healthy, False otherwise.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
            except httpx.HTTPError:
                return False

    async def get_labs(self) -> list[dict]:
        """Get list of available labs.

        Returns:
            List of lab objects.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/items/",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return []

    async def get_scores(self, lab_id: str) -> dict:
        """Get score distribution for a lab.

        Args:
            lab_id: Lab identifier (e.g., "lab-04").

        Returns:
            Score distribution data.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/analytics/scores",
                    params={"lab": lab_id},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return {}
