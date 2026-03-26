"""LMS API client."""

import httpx


class LMSAPIError(Exception):
    """Exception raised when LMS API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


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
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    async def health_check(self) -> dict:
        """Check if the backend is healthy and get item count.

        Returns:
            Dict with 'healthy' bool and 'item_count' int.

        Raises:
            LMSAPIError: If backend is unavailable.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/items/",
                    headers=self._headers,
                )
                response.raise_for_status()
                items = response.json()
                return {"healthy": True, "item_count": len(items)}
            except httpx.ConnectError as e:
                raise LMSAPIError(
                    f"Connection refused ({self.base_url}). "
                    "Check that the backend service is running."
                ) from e
            except httpx.TimeoutException as e:
                raise LMSAPIError(
                    "Request timed out. The backend may be overloaded."
                ) from e
            except httpx.HTTPStatusError as e:
                raise LMSAPIError(
                    f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                    "The backend service may be down."
                ) from e
            except httpx.HTTPError as e:
                raise LMSAPIError(f"HTTP error: {type(e).__name__}") from e

    async def get_labs(self) -> list[dict]:
        """Get list of available labs.

        Returns:
            List of lab objects (type: lab).

        Raises:
            LMSAPIError: If backend is unavailable.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/items/",
                    headers=self._headers,
                )
                response.raise_for_status()
                items = response.json()
                # Filter only labs (not tasks)
                return [item for item in items if item.get("type") == "lab"]
            except httpx.ConnectError as e:
                raise LMSAPIError(
                    f"Connection refused ({self.base_url}). "
                    "Check that the backend service is running."
                ) from e
            except httpx.TimeoutException as e:
                raise LMSAPIError(
                    "Request timed out. The backend may be overloaded."
                ) from e
            except httpx.HTTPStatusError as e:
                raise LMSAPIError(
                    f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                    "The backend service may be down."
                ) from e
            except httpx.HTTPError as e:
                raise LMSAPIError(f"HTTP error: {type(e).__name__}") from e

    async def get_pass_rates(self, lab_id: str) -> list[dict]:
        """Get pass rates for a specific lab.

        Args:
            lab_id: Lab identifier (e.g., "lab-04").

        Returns:
            List of pass rate objects with task info.

        Raises:
            LMSAPIError: If backend is unavailable or lab not found.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/analytics/pass-rates",
                    params={"lab": lab_id},
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError as e:
                raise LMSAPIError(
                    f"Connection refused ({self.base_url}). "
                    "Check that the backend service is running."
                ) from e
            except httpx.TimeoutException as e:
                raise LMSAPIError(
                    "Request timed out. The backend may be overloaded."
                ) from e
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise LMSAPIError(f"Lab '{lab_id}' not found.") from e
                raise LMSAPIError(
                    f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                    "The backend service may be down."
                ) from e
            except httpx.HTTPError as e:
                raise LMSAPIError(f"HTTP error: {type(e).__name__}") from e
