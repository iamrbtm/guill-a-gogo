from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from sqlalchemy.orm import Session
from werkzeug.exceptions import Unauthorized

from app.config import get_settings
from app.models.accounts import Trip
from app.models.itinerary import ChangeProposal
from app.services.providers.routing import ProviderUnavailable


class AISuggestion(BaseModel):
    type: str = Field(..., description="e.g. day_division, stop, meal, summary")
    target: Optional[str] = None
    detail: str


class AIProposalOutput(BaseModel):
    """Strict schema for any AI-generated plan proposal.

    The AI may explain, recommend, and summarize, but it may NOT perform
    arithmetic or assert live facts. Suggestions are structured and must be
    approved by a human before anything changes.
    """

    model_config = {"extra": "forbid"}

    summary: str
    suggestions: list[AISuggestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def validate_ai_output(data: dict) -> AIProposalOutput:
    """Validate untrusted AI JSON. Raises ValidationError on bad shape."""
    return AIProposalOutput.model_validate(data)


def _provider_client(settings):
    if settings.ai_provider in (None, "none"):
        raise ProviderUnavailable("ai_disabled")
    # OpenAI-compatible endpoint expected; real HTTP call is intentionally not
    # implemented here. Point AI_BASE_URL/AI_API_KEY at your compatible gateway.
    return settings


def build_ai_proposal(
    session: Session, trip: Trip, output: AIProposalOutput, user, *, title: str = "AI proposal"
) -> ChangeProposal:
    """Persist an AI proposal as a PENDING change. Never mutates the itinerary."""
    proposal = ChangeProposal(
        trip_id=trip.id,
        kind="ai_proposal",
        title=title,
        before={},
        after=output.model_dump(),
        assumptions=output.assumptions,
        warnings=output.warnings,
        status="pending",
        created_by=user.id,
    )
    session.add(proposal)
    session.flush()
    return proposal


def generate_ai_proposal(
    session: Session, trip: Trip, inputs: dict, user
) -> ChangeProposal:
    """Entry point for the AI proposal route.

    Raises ProviderUnavailable when AI is disabled. When enabled, it would call
    the provider and validate the response; the actual network call is left to the
    configured gateway and is not auto-applied.
    """
    settings = get_settings()
    _provider_client(settings)  # raises if disabled
    # Without a live call we cannot fabricate output; surface that explicitly.
    raise ProviderUnavailable("ai provider call not implemented in this build; set outputs via validated payload")
