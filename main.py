#!/usr/bin/env python3
"""
Idea Validation Agent - Main Entry Point

Human-in-the-loop idea validation agent on Masumi Network.
Accepts a single idea, asks dynamic clarifying questions via /provide_input,
then produces a VC-style validation report with review/refine loop.
"""
# Load environment variables from .env file
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
import uvicorn

# Load .env from the script's directory (explicit path for background processes)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# CrewAI: disable interactive trace prompts in server logs; optional in .env
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")


def _assert_supported_python_version() -> None:
    """Fail fast with a clear message for unsupported CrewAI runtimes."""
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10) or (major, minor) >= (3, 14):
        version = f"{major}.{minor}"
        raise RuntimeError(
            "This agent requires Python >=3.10 and <3.14 because CrewAI "
            f"does not support Python {version}. Use Python 3.13 for local "
            "runs and deployments."
        )


_assert_supported_python_version()

# Register CrewAI Anthropic mitigations at import time (not only on lazy import inside
# process_job) so ``masumi run`` / uvicorn always patch before any LLM call.
import crew_definition  # noqa: F401,E402


def _prefer_local_masumi_package() -> Optional[Path]:
    """Use the sibling pip-masumi checkout when it is available locally."""
    local_checkout = Path(__file__).resolve().parents[2] / "pip-masumi"
    package_init = local_checkout / "masumi" / "__init__.py"
    if not package_init.exists():
        return None

    local_checkout_str = str(local_checkout)
    if local_checkout_str not in sys.path:
        sys.path.insert(0, local_checkout_str)

    return local_checkout


_LOCAL_MASUMI_CHECKOUT = _prefer_local_masumi_package()

logger = logging.getLogger(__name__)


class _CompatibleStartJobRequest(BaseModel):
    """Accept both current and legacy Masumi /start_job payload shapes."""

    model_config = ConfigDict(extra="allow")

    identifier_from_purchaser: str = Field(default="")
    input_data: Optional[Dict[str, Any]] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _normalize_request(cls, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise ValueError("Request body must be an object")

        identifier = (
            raw.get("identifier_from_purchaser")
            or raw.get("identifierFromPurchaser")
            or raw.get("identifier")
            or raw.get("nonce")
        )
        input_data = (
            raw.get("input_data")
            if "input_data" in raw
            else raw.get("inputData")
            if "inputData" in raw
            else raw.get("input")
            if "input" in raw
            else raw.get("inputDataObject")
        )

        if input_data is None:
            normalized_input_data = None
        elif isinstance(input_data, dict):
            normalized_input_data = input_data
        elif isinstance(input_data, list):
            normalized: Dict[str, Any] = {}
            for item in input_data:
                if not isinstance(item, dict):
                    raise ValueError(
                        "input_data list items must be objects"
                    )
                key = item.get("key") or item.get("id") or item.get("field") or item.get("name")
                if key is None:
                    raise ValueError(
                        "input_data list items must contain one of: key, id, field, name"
                    )
                normalized[str(key)] = item.get("value")
            normalized_input_data = normalized
        else:
            raise ValueError("input_data must be an object or array of key/value pairs")

        if identifier is None:
            identifier = uuid.uuid4().hex[:24]
            logger.warning(
                "Missing purchaser identifier in /start_job request; generated fallback identifier=%s",
                identifier,
            )

        logger.info(
            "Normalized /start_job request using compatibility layer: identifier_present=%s input_data_type=%s",
            True,
            type(normalized_input_data).__name__ if normalized_input_data is not None else "None",
        )

        return {
            "identifier_from_purchaser": str(identifier),
            "input_data": normalized_input_data,
        }


def _enable_masumi_start_job_compatibility() -> None:
    """Patch Masumi's request model so old marketplace payloads still work."""
    import masumi
    import masumi.models
    import masumi.server

    if _LOCAL_MASUMI_CHECKOUT is not None:
        logger.info(
            "Using local Masumi package checkout from %s (imported module: %s)",
            _LOCAL_MASUMI_CHECKOUT,
            getattr(masumi, "__file__", "<unknown>"),
        )
    else:
        logger.info(
            "Using installed Masumi package from %s",
            getattr(masumi, "__file__", "<unknown>"),
        )

    masumi.models.StartJobRequest = _CompatibleStartJobRequest
    masumi.server.StartJobRequest = _CompatibleStartJobRequest


_enable_masumi_start_job_compatibility()

from masumi import create_masumi_app
from masumi.config import Config
from agent import process_job
from config import get_settings
from schemas.input_schema import INPUT_SCHEMA


def _build_app():
    settings = get_settings()
    app = create_masumi_app(
        config=Config(
            payment_service_url=settings.payment_service_url,
            payment_api_key=settings.payment_api_key or "",
        ),
        agent_identifier=settings.agent_identifier,
        network=settings.network,
        seller_vkey=settings.seller_vkey,
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA,
    )

    @app.exception_handler(RequestValidationError)
    async def _log_request_validation_error(request: Request, exc: RequestValidationError):
        try:
            body_text = (await request.body()).decode("utf-8", errors="replace")
        except Exception as body_error:  # pragma: no cover - defensive logging path
            body_text = f"<failed to read body: {body_error}>"

        if len(body_text) > 4000:
            body_text = body_text[:4000] + "...<truncated>"

        logger.error(
            "Request validation failed for %s %s with errors=%s body=%s",
            request.method,
            request.url.path,
            exc.errors(),
            body_text,
        )
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    return app


app = _build_app()


def _run_app() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError:
        logger.warning("Invalid PORT value %r; falling back to 8080", os.getenv("PORT"))
        port = 8080

    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print("\n" + "=" * 70)
    print("Starting Idea Validation Agent (Masumi)...")
    print("=" * 70)
    print(f"API Documentation:        http://{display_host}:{port}/docs")
    print(f"Availability Check:       http://{display_host}:{port}/availability")
    print(f"Input Schema:             http://{display_host}:{port}/input_schema")
    print(f"Start Job:                http://{display_host}:{port}/start_job")
    print("=" * 70 + "\n")

    uvicorn.run(app, host=host, port=port, log_level="info")

# Main entry point
if __name__ == "__main__":
    _run_app()
