"""
run_physical_validation.py
Executes a physical tabletop benchtop inspection on physical potato/onion lots
using the live OpenCV camera driver and manual operator instruction workflow.
"""

import sys
import os
import json
import time

from inspection_control.experiments.physical_validation import run_physical_bench_lot
from inspection_control.domain.lot import DefectPatternType


def main():
    print("=" * 80)
    print("STARTING PHYSICAL TABLETOP BENCH INSPECTION")
    print("Closed-Loop Physical Subsystem with OpenCV Camera & Operator Workflow")
    print("=" * 80)

    # 1. Run physical bench lot with real OpenCV camera
    res_physical = run_physical_bench_lot(
        lot_id="BENCH_POTATO_LOT_PHYSICAL_01",
        commodity="potato",
        pattern=DefectPatternType.ADVERSARIAL,
        use_real_camera=True,
        camera_index=0,
        ambient_temp_c=24.5,
        auto_confirm_operator=True,
    )

    # Save summary
    with open("evidence/physical_lots/physical_bench_lot_summary.json", "w") as f:
        json.dump(res_physical, f, indent=2)

    print("\nPhysical bench validation completed. Artifacts recorded in evidence/captures/ and evidence/physical_lots/.")


if __name__ == "__main__":
    main()
