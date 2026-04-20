"""Async HTTP client for the Sokosumi v1 marketplace API.

Implements only the surface area the VC Validation Agent needs to HIRE other
agents on Sokosumi using its OWN bearer key (which is backed by the agent's
own credit balance):

  GET  /v1/agents/{id}/input-schema   - discover the schema of the target
  POST /v1/agents/{id}/jobs            - create (purchase) a job
  GET  /v1/jobs/{id}                   - poll for status + result

Auth: ``Authorization: Bearer <SOKOSUMI_API_KEY>``.

The default base URL is the Preprod testing environment
(``https://preprod.sokosumi.com/api/v1``); switch to ``https://sokosumi.com/api/v1``
for Mainnet via the ``SOKOSUMI_API_URL`` env var.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Sokosumi job statuses we treat as terminal (see Job schema in v1.json).
_TERMINAL_SUCCESS_STATUSES = {"completed"}
_TERMINAL_FAILURE_STATUSES = {
    "failed",
    "payment_failed",
    "refund_pending",
    "refund_resolved",
    "dispute_pending",
    "dispute_resolved",
}


class SokosumiAPIError(RuntimeError):
    """Raised when Sokosumi returns a non-2xx response we cannot recover from."""

    def __init__(self, status_code: int, message: str, body: Any = None) -> None:
        super().__init__(f"Sokosumi API error {status_code}: {message}")
        self.status_code = status_code
        self.body = body


class SokosumiClient:
    """Minimal async Sokosumi marketplace client.

    Designed to be created per-job (or reused) inside an asyncio event loop.
    Always close it via ``await client.aclose()`` (or use ``async with``).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://preprod.sokosumi.com/api/v1",
        *,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("SOKOSUMI_API_KEY is required to use SokosumiClient")

        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> "SokosumiClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ HTTP
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            response = await self._client.request(method, path, json=json_body)
        except httpx.HTTPError as exc:
            raise SokosumiAPIError(0, f"network error: {exc}") from exc

        if response.status_code >= 400:
            try:
                body: Any = response.json()
            except Exception:  # pragma: no cover - defensive
                body = response.text
            message = ""
            if isinstance(body, dict):
                message = body.get("message") or body.get("error") or ""
            raise SokosumiAPIError(
                response.status_code,
                message or response.reason_phrase or "request failed",
                body=body,
            )

        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise SokosumiAPIError(
                response.status_code, f"invalid JSON: {exc}", body=response.text
            ) from exc

        if not isinstance(payload, dict):
            raise SokosumiAPIError(
                response.status_code,
                "expected JSON object response",
                body=payload,
            )
        return payload

    # -------------------------------------------------------------- API ops
    async def get_input_schema(self, agent_id: str) -> Dict[str, Any]:
        """Fetch the live input schema for ``agent_id``.

        Returns the inner ``data`` object as the API documents
        (``{"input_data": [...]}``) so callers can pass it directly back as
        ``inputSchema`` when creating a job.
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        payload = await self._request("GET", f"/agents/{agent_id}/input-schema")
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise SokosumiAPIError(
                200, "input schema response missing 'data' object", body=payload
            )
        return data

    async def create_job(
        self,
        agent_id: str,
        *,
        input_schema: Dict[str, Any],
        input_data: Dict[str, Any],
        max_credits: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create (and pay for) a new job on the target agent.

        Returns the inner ``data`` object — a JobSummary with at minimum
        ``id``, ``status``, and ``credits``.
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        if not input_schema:
            raise ValueError("input_schema is required (echo back what /input-schema returned)")
        if input_data is None:
            input_data = {}

        body: Dict[str, Any] = {
            "inputSchema": input_schema,
            "inputData": input_data,
        }
        if max_credits is not None and max_credits > 0:
            body["maxCredits"] = max_credits
        if name:
            body["name"] = name[:80]  # Sokosumi enforces a max length of 80

        payload = await self._request("POST", f"/agents/{agent_id}/jobs", json_body=body)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise SokosumiAPIError(
                200, "create job response missing 'data' object", body=payload
            )
        return data

    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """Fetch the latest state of a job."""
        if not job_id:
            raise ValueError("job_id is required")
        payload = await self._request("GET", f"/jobs/{job_id}")
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise SokosumiAPIError(
                200, "get job response missing 'data' object", body=payload
            )
        return data

    async def wait_for_job(
        self,
        job_id: str,
        *,
        poll_interval_seconds: int = 15,
        timeout_seconds: int = 900,
    ) -> Dict[str, Any]:
        """Poll ``GET /jobs/{id}`` until the job reaches a terminal state.

        Args:
            job_id: Sokosumi job id.
            poll_interval_seconds: Pause between polls. Sokosumi recommends
                no more aggressive than 10s.
            timeout_seconds: Total wall-clock budget. Defaults to 15 min,
                matching the user-stated wait window for the v1.0.2 hire flow.

        Raises:
            SokosumiAPIError: on terminal failure or HTTP errors.
            asyncio.TimeoutError: if ``timeout_seconds`` elapses without a
                terminal state.
        """
        async def _poll_loop() -> Dict[str, Any]:
            attempts = 0
            while True:
                attempts += 1
                job = await self.get_job(job_id)
                status = str(job.get("status") or "").lower()
                logger.info(
                    "Sokosumi job %s status=%s (poll #%d)",
                    job_id,
                    status or "unknown",
                    attempts,
                )

                if status in _TERMINAL_SUCCESS_STATUSES:
                    return job
                if status in _TERMINAL_FAILURE_STATUSES:
                    raise SokosumiAPIError(
                        200,
                        f"job {job_id} reached terminal failure state '{status}'",
                        body=job,
                    )

                await asyncio.sleep(max(1, poll_interval_seconds))

        return await asyncio.wait_for(_poll_loop(), timeout=max(1, timeout_seconds))
