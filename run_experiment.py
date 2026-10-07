"""
run_experiment.py
Unified Command-Line Interface for Reproducible Closed-Loop Inspection Experiments.
Supports both Physical Bench Mode and High-Throughput Simulation Mode.
"""

import argparse
import sys
import os
import uuid
import json

from run_simulation_validation import main as run_simulation
from run_physical_validation import main as run_physical
from export_results import export_all


def main():
    parser = argparse.ArgumentParser(description="Closed-Loop Physical Inspection Experiment CLI")
    parser.add_argument("--mode", choices=["simulation", "physical", "all"], default="all", help="Execution mode")
    parser.add_argument("--seed", type=int, default=42000, help="Random seed for reproducibility")
    parser.add_argument("--lot-id", type=str, default=None, help="Explicit lot ID")
    parser.add_argument("--camera-index", type=int, default=0, help="OpenCV camera device index")
    args = parser.parse_args()

    exp_id = f"EXP_{uuid.uuid4().hex[:8].upper()}"
    print(f"=======================================================")
    print(f"EXPERIMENT RUNNER | ID: {exp_id}")
    print(f"Mode: {args.mode.upper()} | Seed: {args.seed}")
    print(f"=======================================================\n")

    if args.mode in ("simulation", "all"):
        print("[STAGE 1] Running High-Throughput Simulation Validation...")
        run_simulation()

    if args.mode in ("physical", "all"):
        print("\n[STAGE 2] Running Physical Benchtop Validation with Real Camera...")
        run_physical()

    print("\n[STAGE 3] Exporting Data and Logs...")
    export_all()

    print(f"\n=======================================================")
    print(f"EXPERIMENT {exp_id} COMPLETED SUCCESSFULLY.")
    print(f"=======================================================")


if __name__ == "__main__":
    main()
