"""
inspection_control/api/routes.py
REST endpoints for tabletop inspection station and live dashboard.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time

from inspection_control.domain.lot import BulkLot, DefectPatternType
from inspection_control.station.hardware_interface import PhysicalInspectionStation
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner
from inspection_control.domain.access_graph import PhysicalActionType, AccessAction


router = APIRouter(prefix="/api/station", tags=["station"])

# Session state container
station_instance: Optional[PhysicalInspectionStation] = None
active_lot: Optional[BulkLot] = None
planner_instance: Optional[ExposureAwareInspectionPlanner] = None
current_recommended_action: Optional[AccessAction] = None
current_telemetry: Dict[str, Any] = {}
audit_timeline: List[Dict[str, Any]] = []


class LotInitRequest(BaseModel):
    lot_id: str = "BENCH_LOT_001"
    commodity: str = "potato"
    pattern: str = "ADVERSARIAL"
    use_real_camera: bool = False
    camera_index: int = 0
    ambient_temp_c: float = 25.0


class OperatorActionRequest(BaseModel):
    action_command: str  # "EXECUTE", "SKIP", "STOP", "OVERRIDE"
    override_comment: Optional[str] = None


@router.post("/initialize")
def initialize_lot(req: LotInitRequest):
    global station_instance, active_lot, planner_instance, audit_timeline, current_recommended_action, current_telemetry
    
    pat_enum = getattr(DefectPatternType, req.pattern, DefectPatternType.ADVERSARIAL)
    active_lot = BulkLot(
        lot_id=req.lot_id,
        commodity=req.commodity,
        pattern=pat_enum,
        n_strata=5,
        units_per_stratum=40,
        initial_temp_c=12.0,
    )
    
    station_instance = PhysicalInspectionStation(
        use_real_camera=req.use_real_camera,
        camera_index=req.camera_index,
        manual_auto_confirm=True,
    )
    
    planner_instance = ExposureAwareInspectionPlanner()
    audit_timeline = []

    # Plan first action
    current_recommended_action, current_telemetry = planner_instance.select_next_action(
        lot=active_lot,
        remaining_budget_inr=60.0,
        elapsed_time_sec=0.0,
        ambient_temp_c=req.ambient_temp_c,
    )

    return {
        "status": "INITIALIZED",
        "lot_id": req.lot_id,
        "commodity": req.commodity,
        "n_strata": active_lot.n_strata,
        "recommended_action": current_recommended_action.name,
    }


@router.get("/state")
def get_live_station_state():
    global active_lot, station_instance, current_recommended_action, current_telemetry, audit_timeline
    if not active_lot or not station_instance:
        return {"status": "UNINITIALIZED"}

    # Compile stratum map
    strata_data = []
    for sid, s in active_lot.strata.items():
        rec = active_lot.exposure_ledger.strata_records.get(sid)
        strata_data.append({
            "stratum_id": sid,
            "name": s.name,
            "accessible": sid in active_lot.access_graph.accessible_strata,
            "is_open": sid in active_lot.access_graph.open_strata,
            "expected_defect_pct": round(s.expected_defect_rate * 100.0, 1),
            "defect_variance": round(s.defect_variance, 4),
            "observation_confidence": round(s.observation_confidence, 2),
            "cumulative_exposure_sec": round(rec.cumulative_exposure_time_sec, 1) if rec else 0.0,
            "exposure_stage": rec.exposure_state.value if rec else "SEALED",
            "times_opened": rec.times_opened if rec else 0,
        })

    core_t = station_instance.get_current_temperature(0)
    amb_t = station_instance.get_ambient_temperature()
    cum_lot_exposure = sum(r.cumulative_exposure_time_sec for r in active_lot.exposure_ledger.strata_records.values())

    return {
        "lot_id": active_lot.lot_id,
        "commodity": active_lot.commodity,
        "core_temp_c": core_t,
        "ambient_temp_c": amb_t,
        "cumulative_lot_exposure_sec": round(cum_lot_exposure, 1),
        "strata": strata_data,
        "recommended_action": {
            "name": current_recommended_action.name if current_recommended_action else "STOP",
            "action_type": current_recommended_action.action_type.value if current_recommended_action else "STOP",
            "target_stratum": current_recommended_action.target_stratum_id if current_recommended_action else 0,
            "cost_inr": current_recommended_action.physical_cost_inr if current_recommended_action else 0.0,
            "reason": current_telemetry.get("reason", "PLANNER_SELECTION"),
        },
        "audit_timeline": audit_timeline[-10:],
    }


@router.post("/execute_step")
def execute_operator_step(req: OperatorActionRequest):
    global active_lot, station_instance, planner_instance, current_recommended_action, current_telemetry, audit_timeline
    if not active_lot or not current_recommended_action:
        raise HTTPException(status_code=400, detail="No active inspection lot")

    amb_t = station_instance.get_ambient_temperature()
    act = current_recommended_action

    if req.action_command == "STOP" or act.action_type == PhysicalActionType.STOP_INSPECTION:
        disposition = planner_instance.recommend_terminal_disposition(active_lot)
        teardown = active_lot.get_ground_truth_for_teardown()
        
        audit_timeline.append({
            "step": len(audit_timeline) + 1,
            "action": "STOP_INSPECTION",
            "terminal_disposition": disposition.value,
            "true_defect_rate": round(teardown.overall_true_defect_rate * 100, 1),
            "timestamp": time.time(),
        })
        current_recommended_action = None
        return {
            "status": "TERMINATED",
            "terminal_disposition": disposition.value,
            "true_overall_defect_rate": teardown.overall_true_defect_rate,
        }

    # Execute physical instruction
    op_event = station_instance.execute_access_instruction(active_lot, act)

    # If observation action, capture frame
    obs_info = {}
    if act.action_type in (PhysicalActionType.OBSERVE_STRATUM, PhysicalActionType.SAMPLE_UNITS):
        obs = station_instance.capture_observation(active_lot, act.target_stratum_id)
        active_lot.strata[act.target_stratum_id].belief_alpha += (obs.units_observed * obs.defect_probability * obs.confidence)
        active_lot.strata[act.target_stratum_id].belief_beta += (obs.units_observed * (1.0 - obs.defect_probability) * obs.confidence)
        obs_info = {
            "defect_pct": round(obs.defect_probability * 100, 1),
            "confidence": round(obs.confidence, 2),
            "image_path": obs.image_path,
        }

    audit_timeline.append({
        "step": len(audit_timeline) + 1,
        "action": act.name,
        "operator": req.action_command,
        "observation": obs_info,
        "timestamp": time.time(),
    })

    # Replan next action
    current_recommended_action, current_telemetry = planner_instance.select_next_action(
        lot=active_lot,
        remaining_budget_inr=50.0,
        elapsed_time_sec=float(len(audit_timeline) * 15.0),
        ambient_temp_c=amb_t,
    )

    return {
        "status": "STEP_COMPLETED",
        "next_action": current_recommended_action.name if current_recommended_action else "STOP",
    }
