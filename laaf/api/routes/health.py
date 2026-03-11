"""Health and metrics endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

import laaf
from laaf.api.models import HealthResponse
from laaf.taxonomy.base import get_registry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        version=laaf.__version__,
        techniques_loaded=len(get_registry()),
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/metrics")
async def metrics():
    """Prometheus-style text metrics (basic)."""
    registry = get_registry()
    lines = [
        f"# HELP laaf_techniques_total Total techniques in registry",
        f"# TYPE laaf_techniques_total gauge",
        f"laaf_techniques_total {len(registry)}",
    ]
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines))
