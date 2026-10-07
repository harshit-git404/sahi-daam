"""
inspection_control/mechanical/mechanical_state.py
Mechanical Stratum State and Mechanical History Ledger.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import copy
import numpy as np


@dataclass
class MechanicalStratumState:
    """Dynamic mechanical and physical state for a single stratum."""
    stratum_id: int
    name: str
    mass_kg: float
    stiffness_n_per_cm: float
    deformation_susceptibility: float
    is_present: bool = True
    is_accessible: bool = False
    is_open: bool = False
    is_observed: bool = False
    
    # Instantaneous mechanical dynamics
    force_n: float = 0.0
    compression_cm: float = 0.0
    displacement_cm: float = 0.0
    
    # Path-dependent mechanical memory
    accumulated_load_n_sec: float = 0.0
    peak_force_n: float = 0.0
    residual_deformation_cm: float = 0.0
    recovery_fraction: float = 0.0
    
    # Observation & condition coupling states
    visual_occlusion_factor: float = 0.0
    mechanical_bruising_delta: float = 0.0

    # Ground truth (isolated from planner)
    true_defect_rate: float = 0.0
    units_defective: int = 0
    units_total: int = 50

    def copy(self) -> "MechanicalStratumState":
        return copy.deepcopy(self)


@dataclass
class MechanicalHistorySnapshot:
    """Timestamped snapshot of lot mechanical loading."""
    timestamp_sec: float
    action_name: str
    forces: List[float]
    compressions: List[float]
    residual_deformations: List[float]
    present_mask: List[bool]


class MechanicalStateLedger:
    """
    Tracks trajectory of mechanical states, loading history, and structural events.
    """

    def __init__(self, lot_id: str, n_strata: int = 5):
        self.lot_id = lot_id
        self.n_strata = n_strata
        self.snapshots: List[MechanicalHistorySnapshot] = []
        self.total_mechanical_work_joules: float = 0.0
        self.peak_stack_stress_kpa: float = 0.0

    def record_step(
        self,
        timestamp_sec: float,
        action_name: str,
        strata: Dict[int, MechanicalStratumState],
    ) -> None:
        forces = [strata[i].force_n if strata[i].is_present else 0.0 for i in range(self.n_strata)]
        compressions = [strata[i].compression_cm if strata[i].is_present else 0.0 for i in range(self.n_strata)]
        res_defs = [strata[i].residual_deformation_cm if strata[i].is_present else 0.0 for i in range(self.n_strata)]
        present = [strata[i].is_present for i in range(self.n_strata)]

        snap = MechanicalHistorySnapshot(
            timestamp_sec=timestamp_sec,
            action_name=action_name,
            forces=forces,
            compressions=compressions,
            residual_deformations=res_defs,
            present_mask=present,
        )
        self.snapshots.append(snap)
