"""v1.0.2 — Sokosumi orchestration layer.

This package lets the VC Validation Agent hire OTHER agents listed on the
Sokosumi marketplace, wait for their results, and feed those results back
into its own VC analysis. The agent pays out of its own Sokosumi credit
balance using the SOKOSUMI_API_KEY bearer token.
"""

from .sokosumi_client import SokosumiClient, SokosumiAPIError
from .agent_hiring import (
    HiredAgentResult,
    OrchestrationOutcome,
    run_external_research_orchestration,
)

__all__ = [
    "SokosumiClient",
    "SokosumiAPIError",
    "HiredAgentResult",
    "OrchestrationOutcome",
    "run_external_research_orchestration",
]
