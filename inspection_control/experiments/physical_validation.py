"""
inspection_control/experiments/physical_validation.py
Real Tabletop Physical Bench Validation Protocol.
Drives real camera acquisition, physical strata unstacking, operator confirmations,
and post-inspection physical teardown grading for potato/onion lots.
"""

from typing import Dict, Any, List, Optional
import time
import os

from inspection_control.domain.lot import BulkLot, DefectPatternType
from inspection_control.station.hardware_interface import PhysicalInspectionStation
from inspection_control.planning.exposure_aware_planner import ExposureAwareInspectionPlanner
from inspection_control.experiments.runner import InspectionEpisodeRunner


def run_physical_bench_lot(
    lot_id: str,
    commodity: str = "potato",
    pattern: DefectPatternType = DefectPatternType.ADVERSARIAL,
    use_real_camera: bool = True,
    camera_index: int = 0,
    ambient_temp_c: float = 24.5,
    auto_confirm_operator: bool = True,
) -> Dict[str, Any]:
    """
    Executes a real physical benchtop lot inspection using connected camera hardware.
    """
    os.makedirs("evidence/captures", exist_ok=True)
    os.makedirs("evidence/physical_lots", exist_ok=True)

    print(f"\n=======================================================")
    print(f"STARTING PHYSICAL BENCH LOT: {lot_id} ({commodity.upper()})")
    print(f"Camera Hardware Mode: {'REAL OPENCV (INDEX ' + str(camera_index) + ')' if use_real_camera else 'MOCK SIMULATION'}")
    print(f"Operational Pattern: {pattern.value}")
    print(f"=======================================================\n")

    # 1. Initialize physical station
    station = PhysicalInspectionStation(
        use_real_camera=use_real_camera,
        camera_index=camera_index,
        manual_auto_confirm=auto_confirm_operator,
    )

    # 2. Build physical lot abstraction
    lot = BulkLot(
        lot_id=lot_id,
        commodity=commodity,
        pattern=pattern,
        n_strata=5,
        units_per_stratum=40,
        initial_temp_c=12.5,
    )

    # 3. Instantiate controller
    planner = ExposureAwareInspectionPlanner(name="FB7_Physical_Bench_Controller")

    # 4. Execute closed loop
    runner = InspectionEpisodeRunner(station=station)
    episode_result = runner.run_episode(
        lot=lot,
        planner=planner,
        initial_budget_inr=70.0,
        ambient_temp_c=ambient_temp_c,
    )

    # Clean up hardware
    station.release()

    print(f"\n[PHYSICAL BENCH TEARDOWN COMPLETED]")
    print(f"  Chosen Disposition: {episode_result['chosen_disposition']}")
    print(f"  True Defect Rate: {episode_result['true_overall_defect_rate'] * 100:.1f}%")
    print(f"  Estimated Defect Rate: {episode_result['estimated_defect_rate'] * 100:.1f}%")
    print(f"  Total Disposition Loss: INR {episode_result['total_disposition_loss']}")
    print(f"  Cumulative Exposure Time: {episode_result['cumulative_exposure_sec']}s")
    print(f"  Actions Executed: {episode_result['action_sequence']}")

    return episode_result
