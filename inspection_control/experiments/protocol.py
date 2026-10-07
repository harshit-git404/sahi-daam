"""
inspection_control/experiments/protocol.py
Formal Experimental Protocols, Operational Regimes, and the Decisive Non-Additive Test.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from inspection_control.domain.lot import DefectPatternType


@dataclass
class RegimeConfig:
    regime_id: str
    name: str
    description: str
    pattern: DefectPatternType
    ambient_temp_c: float
    initial_lot_temp_c: float
    access_cost_multiplier: float
    deterioration_rate_multiplier: float
    budget_inr: float = 60.0


# Operational Regimes from Part 13
REGIMES: Dict[str, RegimeConfig] = {
    "REGIME_A_UNIFORM": RegimeConfig(
        regime_id="REGIME_A_UNIFORM",
        name="Regime A: Uniform Quality",
        description="Defect prevalence uniformly distributed across all strata (12%-18%).",
        pattern=DefectPatternType.UNIFORM,
        ambient_temp_c=25.0,
        initial_lot_temp_c=14.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
    "REGIME_B_DEPTH_CORRELATED": RegimeConfig(
        regime_id="REGIME_B_DEPTH_CORRELATED",
        name="Regime B: Depth-Correlated Deterioration",
        description="Surface is clean (2%), deeper layers have increasing spoilage.",
        pattern=DefectPatternType.DEPTH_CORRELATED,
        ambient_temp_c=26.0,
        initial_lot_temp_c=12.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
    "REGIME_C_HIDDEN_BOTTOM": RegimeConfig(
        regime_id="REGIME_C_HIDDEN_BOTTOM",
        name="Regime C: Hidden-Bottom Severe Defects",
        description="Strata 0..3 clean (3%), stratum 4 (bottom) harbors severe rot (>45%).",
        pattern=DefectPatternType.HIDDEN_BOTTOM,
        ambient_temp_c=28.0,
        initial_lot_temp_c=12.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.2,
    ),
    "REGIME_D_CLUSTERED": RegimeConfig(
        regime_id="REGIME_D_CLUSTERED",
        name="Regime D: Clustered Internal Defects",
        description="Defects isolated to middle strata S2 and S3.",
        pattern=DefectPatternType.CLUSTERED,
        ambient_temp_c=24.0,
        initial_lot_temp_c=14.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
    "REGIME_E_SURFACE_BIASED": RegimeConfig(
        regime_id="REGIME_E_SURFACE_BIASED",
        name="Regime E: Surface-Biased Presentation",
        description="Upper 2 strata clean (3%), lower strata have moderate defects (25%).",
        pattern=DefectPatternType.SURFACE_BIASED,
        ambient_temp_c=25.0,
        initial_lot_temp_c=13.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
    "REGIME_F_ADVERSARIAL": RegimeConfig(
        regime_id="REGIME_F_ADVERSARIAL",
        name="Regime F: Adversarial Supplier Presentation",
        description="Surface meticulously curated (1%), deeper layers rotten (40%-55%).",
        pattern=DefectPatternType.ADVERSARIAL,
        ambient_temp_c=27.0,
        initial_lot_temp_c=12.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
    "REGIME_G_HIGH_AMBIENT": RegimeConfig(
        regime_id="REGIME_G_HIGH_AMBIENT",
        name="Regime G: High Ambient Thermal Stress",
        description="Ambient temp 34 degC (high thermal shock on opening cold crates).",
        pattern=DefectPatternType.DEPTH_CORRELATED,
        ambient_temp_c=34.0,
        initial_lot_temp_c=10.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=2.5,
    ),
    "REGIME_H_LOW_AMBIENT": RegimeConfig(
        regime_id="REGIME_H_LOW_AMBIENT",
        name="Regime H: Controlled Cold-Chain Ambient",
        description="Ambient temp 14 degC (minimal thermal shock, cheap inspection time).",
        pattern=DefectPatternType.DEPTH_CORRELATED,
        ambient_temp_c=14.0,
        initial_lot_temp_c=12.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=0.4,
    ),
    "REGIME_I_BENIGN_SURFACE": RegimeConfig(
        regime_id="REGIME_I_BENIGN_SURFACE",
        name="Regime I: Benign High Quality",
        description="Entire lot pristine (<3% defect). Correct action is immediate stop.",
        pattern=DefectPatternType.BENIGN,
        ambient_temp_c=22.0,
        initial_lot_temp_c=14.0,
        access_cost_multiplier=1.0,
        deterioration_rate_multiplier=1.0,
    ),
}
