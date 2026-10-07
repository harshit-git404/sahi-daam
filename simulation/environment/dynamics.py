"""
simulation/environment/dynamics.py
State Transition Function T(s_before, a, dt) for Bulk Perishable Lots.

Models physical state alterations caused by inspection:
- Cumulative ambient and thermal exposure
- Quality deterioration over inspection duration
- Cross-strata pathogen contagion and decay transmission
- Physical unit destruction/sampling
- Accessibility and layer removal transitions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from simulation.environment.lot import BulkPerishableLot, StratumState
from simulation.environment.access_graph import ActionType, InspectionAction


@dataclass
class ObservationYield:
    action: InspectionAction
    observed_stratum: int
    data_type: str                   # 'surface_scan', 'unit_samples', 'secondary_probe', 'none'
    sample_qualities: Optional[np.ndarray] = None
    estimated_defect_rate: Optional[float] = None
    sample_count: int = 0
    sensor_variance: float = 0.0
    action_cost: float = 0.0
    deterioration_loss: float = 0.0
    contagion_spread_count: int = 0


@dataclass
class DynamicsConfig:
    optical_sensor_std: float = 0.07       # Surface vision noise
    secondary_probe_std: float = 0.02      # Precision NIR / penetrometer noise
    base_deterioration_rate: float = 0.002 # Quality loss per minute of ambient exposure
    contagion_transmission_rate: float = 0.005 # Defect spread probability per unit time per infected neighbor
    disturbance_contagion_jump: float = 0.015  # Contagion spike when layer is disturbed/moved
    ambient_warming_rate: float = 0.05    # C warming per minute once unsealed


class LotDynamicsEngine:
    """
    Executes state transitions and simulates physical side effects of inspection actions.
    """

    def __init__(self, config: Optional[DynamicsConfig] = None, rng: Optional[np.random.Generator] = None):
        self.config = config or DynamicsConfig()
        self.rng = rng or np.random.default_rng(999)

    def transition(
        self,
        lot: BulkPerishableLot,
        action: InspectionAction,
        removed_strata: Set[int],
        accessible_strata: Set[int],
        exposed_strata: Set[int],
    ) -> Tuple[ObservationYield, Set[int], Set[int], Set[int]]:
        """
        Applies action to lot, mutating physical state according to transition dynamics.
        Returns: (observation_yield, updated_removed, updated_accessible, updated_exposed)
        """
        cfg = self.config
        dt = action.time_minutes
        lot.elapsed_time += dt

        # Baseline physical deterioration across all currently exposed strata
        initial_mean_q = lot.ground_truth_mean_quality

        # Update thermal and exposure states
        for s_id, stratum in lot.strata.items():
            if s_id in exposed_strata:
                stratum.exposure_level += (dt / 10.0)
                stratum.temperature = min(
                    lot.config.ambient_temp,
                    stratum.temperature + (cfg.ambient_warming_rate * dt),
                )
                # Apply quality degradation proportional to exposure and temperature
                temp_factor = max(1.0, stratum.temperature / 15.0)
                quality_decay = cfg.base_deterioration_rate * dt * temp_factor
                stratum.qualities = np.clip(stratum.qualities - quality_decay, 0.0, 1.0)

        # Contagion dynamics: rot spreads from high-defect strata to adjacent strata
        contagion_events = 0
        for s_id in range(lot.config.n_strata):
            current = lot.strata[s_id]
            if current.defect_prevalence > 0.25:
                # Contagion pressure to adjacent strata (s_id - 1 and s_id + 1)
                for neighbor_id in [s_id - 1, s_id + 1]:
                    if 0 <= neighbor_id < lot.config.n_strata:
                        neighbor = lot.strata[neighbor_id]
                        spread_prob = cfg.contagion_transmission_rate * dt * (current.defect_prevalence)
                        if self.rng.random() < spread_prob:
                            # Contagion infects random good units in neighbor
                            good_indices = np.where(neighbor.qualities >= 0.5)[0]
                            if len(good_indices) > 0:
                                infect_count = min(len(good_indices), self.rng.integers(1, 4))
                                target_units = self.rng.choice(good_indices, size=infect_count, replace=False)
                                neighbor.qualities[target_units] = self.rng.uniform(0.15, 0.40, size=infect_count)
                                contagion_events += infect_count

        post_mean_q = lot.ground_truth_mean_quality
        deterioration_loss = max(0.0, (initial_mean_q - post_mean_q) * lot.total_remaining_units * 5.0)

        # Process specific action mechanics
        new_removed = set(removed_strata)
        new_accessible = set(accessible_strata)
        new_exposed = set(exposed_strata)

        if action.action_type == ActionType.STOP_INSPECTION:
            yield_data = ObservationYield(
                action=action,
                observed_stratum=0,
                data_type="none",
                sensor_variance=0.0,
                action_cost=action.cost,
                deterioration_loss=deterioration_loss,
            )
            return yield_data, new_removed, new_accessible, new_exposed

        elif action.action_type == ActionType.REMOVE_LAYER:
            target_s = action.target_stratum
            new_removed.add(target_s)
            next_s = target_s + 1
            if next_s < lot.config.n_strata:
                new_accessible.add(next_s)
                new_exposed.add(next_s)
                lot.strata[next_s].is_accessible = True
                lot.strata[next_s].is_exposed = True
                lot.strata[next_s].exposure_level += 0.5  # Exposure jump
                # Physical disturbance jump
                lot.strata[next_s].contagion_load += cfg.disturbance_contagion_jump

            # ENABLING ACTION YIELDS ZERO IMMEDIATE OBSERVATION
            yield_data = ObservationYield(
                action=action,
                observed_stratum=target_s,
                data_type="none",
                sample_count=0,
                sensor_variance=0.0,
                action_cost=action.cost,
                deterioration_loss=deterioration_loss,
                contagion_spread_count=contagion_events,
            )
            return yield_data, new_removed, new_accessible, new_exposed

        elif action.action_type == ActionType.INSPECT_SURFACE:
            target_s = action.target_stratum
            stratum = lot.strata[target_s]
            stratum.surface_observed = True
            # Surface vision reading with noise
            true_p = stratum.defect_prevalence
            noise = self.rng.normal(0.0, cfg.optical_sensor_std)
            est_p = float(np.clip(true_p + noise, 0.0, 1.0))

            yield_data = ObservationYield(
                action=action,
                observed_stratum=target_s,
                data_type="surface_scan",
                estimated_defect_rate=est_p,
                sensor_variance=cfg.optical_sensor_std ** 2,
                action_cost=action.cost,
                deterioration_loss=deterioration_loss,
                contagion_spread_count=contagion_events,
            )
            return yield_data, new_removed, new_accessible, new_exposed

        elif action.action_type == ActionType.SAMPLE_UNITS:
            target_s = action.target_stratum
            stratum = lot.strata[target_s]
            n_req = action.n_samples
            available_indices = [i for i in range(stratum.n_units) if i not in stratum.sampled_indices]
            n_take = min(n_req, len(available_indices))

            if n_take > 0:
                chosen = self.rng.choice(available_indices, size=n_take, replace=False).tolist()
                stratum.sampled_indices.extend(chosen)
                lot.units_destroyed += n_take
                sample_q = stratum.qualities[chosen].copy()
                est_p = float(np.mean(sample_q < 0.5))
            else:
                sample_q = np.array([])
                est_p = 0.0

            yield_data = ObservationYield(
                action=action,
                observed_stratum=target_s,
                data_type="unit_samples",
                sample_qualities=sample_q,
                sample_count=n_take,
                estimated_defect_rate=est_p,
                sensor_variance=0.01,  # Direct measurement has low measurement error
                action_cost=action.cost,
                deterioration_loss=deterioration_loss,
                contagion_spread_count=contagion_events,
            )
            return yield_data, new_removed, new_accessible, new_exposed

        elif action.action_type == ActionType.SECONDARY_SENSOR:
            target_s = action.target_stratum
            stratum = lot.strata[target_s]
            true_p = stratum.defect_prevalence
            noise = self.rng.normal(0.0, cfg.secondary_probe_std)
            est_p = float(np.clip(true_p + noise, 0.0, 1.0))

            yield_data = ObservationYield(
                action=action,
                observed_stratum=target_s,
                data_type="secondary_probe",
                estimated_defect_rate=est_p,
                sensor_variance=cfg.secondary_probe_std ** 2,
                action_cost=action.cost,
                deterioration_loss=deterioration_loss,
                contagion_spread_count=contagion_events,
            )
            return yield_data, new_removed, new_accessible, new_exposed

        raise ValueError(f"Unrecognized action type: {action.action_type}")
