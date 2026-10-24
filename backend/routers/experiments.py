"""
Experiment Lab Router for Sahi Daam.

Provides endpoints for:
1. Listing predefined pricing simulation scenarios.
2. Executing individual scenario simulations with deterministic mock inputs.
3. Running all scenarios in batch and compiling EXPERIMENT_REPORT.md.
4. Retrieving recorded experiment runs and downloading JSON evidence files.
5. Inspecting the global experiments manifest.

Compatible with direct API requests and Vite dev proxy rewrites (/api).
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Response
from pydantic import BaseModel, Field

from backend.services.experiment_service import (
    ExperimentService,
    EXPERIMENTS_ROOT,
)


router = APIRouter(tags=["Experiment Lab"])


# ---------------------------------------------------------------------------
# DTO Models
# ---------------------------------------------------------------------------
class ScenarioSummaryDTO(BaseModel):
    scenario_id: str
    scenario_name: str
    category: str
    description: str
    commodity_id: str
    wholesale_price: Optional[float] = None
    transport_cost: Optional[float] = None
    transport_status: str
    markup_range: str
    quality_adjustment: int
    raw_observations_count: int
    is_mock: bool = True


class ManifestRunDTO(BaseModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    category: str
    timestamp_utc: str
    status: str
    calculation_status: str
    relative_path: str
    all_checks_passed: bool
    checks_passed_count: int
    checks_total_count: int
    algorithm_version: str
    sha256_hash: str
    is_mock: bool = True


class ManifestDTO(BaseModel):
    schema_version: str = "1.0.0"
    generated_at_utc: str
    total_runs: int
    runs: List[ManifestRunDTO]


# ---------------------------------------------------------------------------
# Scenarios Listing
# ---------------------------------------------------------------------------
@router.get(
    "/experiments/scenarios",
    response_model=List[ScenarioSummaryDTO],
    summary="List all predefined pricing simulation scenarios",
)
@router.get(
    "/api/experiments/scenarios",
    response_model=List[ScenarioSummaryDTO],
    include_in_schema=False,
)
def list_scenarios() -> List[ScenarioSummaryDTO]:
    scenarios = ExperimentService.list_scenarios()
    return [ScenarioSummaryDTO(**s) for s in scenarios]


# ---------------------------------------------------------------------------
# Scenario Execution
# ---------------------------------------------------------------------------
@router.post(
    "/experiments/run/{scenario_id}",
    summary="Execute a controlled pricing scenario simulation",
)
@router.post(
    "/api/experiments/run/{scenario_id}",
    include_in_schema=False,
)
def run_scenario(scenario_id: str) -> Dict[str, Any]:
    try:
        return ExperimentService.run_scenario(scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {exc}") from exc


@router.post(
    "/experiments/run-all",
    summary="Execute all predefined scenarios in batch and generate EXPERIMENT_REPORT.md",
)
@router.post(
    "/api/experiments/run-all",
    include_in_schema=False,
)
def run_all_scenarios() -> Dict[str, Any]:
    try:
        return ExperimentService.run_all_scenarios()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Manifest and Runs History
# ---------------------------------------------------------------------------
@router.get(
    "/experiments/manifest",
    summary="Retrieve the global index manifest of executed experiment runs",
)
@router.get(
    "/api/experiments/manifest",
    include_in_schema=False,
)
def get_manifest() -> Dict[str, Any]:
    manifest_file = EXPERIMENTS_ROOT / "manifest.json"
    if not manifest_file.exists():
        return {
            "schema_version": "1.0.0",
            "generated_at_utc": "",
            "total_runs": 0,
            "runs": [],
        }
    with open(manifest_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/experiments/runs",
    summary="List all recorded experiment runs",
)
@router.get(
    "/api/experiments/runs",
    include_in_schema=False,
)
def list_runs() -> List[Dict[str, Any]]:
    return ExperimentService.list_runs()


@router.get(
    "/experiments/runs/{run_id}",
    summary="Retrieve full evidence payload and calculation steps for a specific experiment run",
)
@router.get(
    "/api/experiments/runs/{run_id}",
    include_in_schema=False,
)
def get_run_detail(run_id: str) -> Dict[str, Any]:
    detail = ExperimentService.get_run_detail(run_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Experiment run '{run_id}' not found.")
    return detail


@router.get(
    "/experiments/runs/{run_id}/export",
    summary="Download the self-contained JSON evidence file for an experiment run",
)
@router.get(
    "/api/experiments/runs/{run_id}/export",
    include_in_schema=False,
)
def export_run_json(run_id: str) -> Response:
    detail = ExperimentService.get_run_detail(run_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Experiment run '{run_id}' not found.")

    content = json.dumps(detail, indent=2, ensure_ascii=False)
    filename = f"{run_id}.json"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/json; charset=utf-8",
    }
    return Response(content=content, media_type="application/json", headers=headers)
