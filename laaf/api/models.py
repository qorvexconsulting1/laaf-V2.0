"""Pydantic models for the LAAF REST API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanRequest(BaseModel):
    target: str = Field(..., description="Platform: openai|anthropic|google|huggingface|mock")
    model: Optional[str] = Field(None, description="Model override")
    stages: list[str] = Field(default=["S1","S2","S3","S4","S5","S6"])
    max_payloads: int = Field(default=100, ge=1, le=5000)
    rate_delay: float = Field(default=2.0, ge=0.1, le=30.0)
    scan_id: Optional[str] = None


class StageResultSchema(BaseModel):
    stage_id: str
    stage_name: str
    broken: bool
    attempts: int
    winning_technique: Optional[str]
    winning_technique_name: Optional[str]
    winning_category: Optional[str]
    confidence: float
    duration_seconds: float
    outcomes: dict[str, int]
    # Artifact evidence
    winning_payload_content: Optional[str] = None
    winning_response: Optional[str] = None
    winning_raw_instruction: Optional[str] = None
    attack_impact: Optional[str] = None


class ScanResultSchema(BaseModel):
    scan_id: str
    platform: str
    model: str
    status: ScanStatus
    created_at: datetime
    completed_at: Optional[datetime]
    total_attempts: int
    stages_broken: int
    breakthrough_rate: float
    stages: list[StageResultSchema]
    error: Optional[str] = None
    attacker_capabilities: list[str] = []
    risk_rating: Optional[str] = None


class ScanListItem(BaseModel):
    scan_id: str
    platform: str
    status: ScanStatus
    created_at: datetime
    stages_broken: int
    breakthrough_rate: float


class HealthResponse(BaseModel):
    status: str
    version: str
    techniques_loaded: int
    timestamp: datetime


class TechniqueSchema(BaseModel):
    id: str
    name: str
    category: str
    lpci_stage: str
    description: str
    tags: list[str]
