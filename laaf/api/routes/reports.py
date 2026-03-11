"""Report download endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from laaf.api.routes.scans import _SCANS
from laaf.api.models import ScanStatus
from laaf.core.stage_breaker import PSBResult, StageResult
from laaf.taxonomy.base import Outcome

router = APIRouter(prefix="/reports", tags=["Reports"])


def _schema_to_psb_result(scan_id: str) -> PSBResult:
    import hashlib
    from laaf.generators.payload_generator import Payload
    schema = _SCANS.get(scan_id)
    if not schema:
        raise HTTPException(404, f"Scan {scan_id!r} not found")
    if schema.status != ScanStatus.COMPLETED:
        raise HTTPException(409, f"Scan {scan_id!r} is not completed yet")

    stages = []
    for s in schema.stages:
        winning_payload = None
        if s.winning_technique:
            winning_payload = Payload(
                id=f"RPT-{hashlib.sha256((s.winning_payload_content or '').encode()).hexdigest()[:8].upper()}",
                raw_instruction=s.winning_raw_instruction or "",
                technique_id=s.winning_technique,
                technique_name=s.winning_technique_name or s.winning_technique,
                category=s.winning_category or "",
                content=s.winning_payload_content or "",
            )
        stages.append(StageResult(
            stage_id=s.stage_id,
            stage_name=s.stage_name,
            broken=s.broken,
            attempts=s.attempts,
            winning_payload=winning_payload,
            winning_outcome=Outcome.EXECUTED if s.broken else Outcome.BLOCKED,
            winning_confidence=s.confidence,
            duration_seconds=s.duration_seconds,
            all_outcomes=s.outcomes,
            winning_payload_content=s.winning_payload_content,
            winning_response=s.winning_response,
            winning_raw_instruction=s.winning_raw_instruction,
        ))
    return PSBResult(
        platform=schema.platform,
        model=schema.model,
        stages=stages,
        total_duration_seconds=0,
        total_attempts=schema.total_attempts,
    )


@router.get("/{scan_id}")
async def get_report(
    scan_id: str,
    format: str = Query("json", description="Report format: json|csv|html|pdf"),
):
    """Download a report for a completed scan."""
    from laaf.reporting import get_reporter

    result = _schema_to_psb_result(scan_id)
    out_dir = Path("results") / scan_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{scan_id}"

    try:
        reporter = get_reporter(format)
        generated = reporter.generate(result, out_path)
    except Exception as exc:
        raise HTTPException(500, f"Report generation failed: {exc}")

    media_types = {
        "json": "application/json",
        "csv": "text/csv",
        "html": "text/html",
        "pdf": "application/pdf",
    }
    return FileResponse(
        path=str(generated),
        media_type=media_types.get(format, "application/octet-stream"),
        filename=generated.name,
    )
