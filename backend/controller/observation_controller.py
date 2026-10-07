"""Adaptive Observation Controller.

The decision centerpiece of the invention. Evaluates the Expected Value of Information (EVI)
against observation acquisition cost to determine whether to request additional visual evidence
or finalize the commodity valuation.
"""

from typing import Optional
from config import settings
from core.schemas import (
    ValuationResult,
    ControllerDecision,
    ControllerAction,
    ObservationRequest,
    ObservationView,
)


class AdaptiveObservationController:
    """
    Decides whether additional observations should be actively acquired.
    
    Value of Information (EVI) Formulation:
    ---------------------------------------
    Let U_curr be the current compound valuation uncertainty.
    Let G_info be the expected fractional information gain from an additional targeted viewpoint
    (e.g., ~0.30 for reverse side inspection; ~0.15 for close-up blemish check).
    Let C_obs be the normalized acquisition cost (user effort/time penalty ~0.08).
    
    The net Expected Value of Information is:
    
        EVI = (U_curr * G_info) - C_obs
        
    Decision Rule:
    --------------
    If EVI > MIN_INFORMATION_GAIN_THRESHOLD
       AND observation_count < MAX_OBSERVATIONS
       AND U_curr > MAX_VALUATION_UNCERTAINTY:
       
         -> ACQUIRE_ADDITIONAL_OBSERVATION (with targeted view prompt)
         
    Else:
         -> FINALIZE_VALUATION
    """

    def __init__(
        self,
        max_observations: int = settings.MAX_OBSERVATIONS,
        observation_cost: float = settings.OBSERVATION_COST,
        evi_threshold: float = settings.MIN_INFORMATION_GAIN_THRESHOLD,
        target_max_uncertainty: float = settings.MAX_VALUATION_UNCERTAINTY,
    ):
        self.max_obs = max_observations
        self.obs_cost = observation_cost
        self.evi_threshold = evi_threshold
        self.target_max_unc = target_max_uncertainty

    def evaluate_observation_decision(
        self,
        valuation: ValuationResult,
        current_observation_count: int = 1,
        force_finalize: bool = False
    ) -> ControllerDecision:
        if force_finalize:
            return ControllerDecision(
                decision=ControllerAction.FINALIZE_VALUATION,
                reason="User or system requested forced finalization.",
                current_uncertainty=valuation.valuation_uncertainty,
                expected_value_of_information=0.0,
                estimated_observation_cost=self.obs_cost,
                threshold=self.evi_threshold,
                observation_request=None,
            )

        # 1. Observation limit boundary check
        if current_observation_count >= self.max_obs:
            return ControllerDecision(
                decision=ControllerAction.FINALIZE_VALUATION,
                reason=f"Maximum observation count ({self.max_obs}) reached; final valuation locked.",
                current_uncertainty=valuation.valuation_uncertainty,
                expected_value_of_information=0.0,
                estimated_observation_cost=self.obs_cost,
                threshold=self.evi_threshold,
                observation_request=None,
            )

        # 2. Confidence sufficiency check
        u_val = valuation.valuation_uncertainty
        u_qual = valuation.quality_estimate.uncertainty

        # If already highly certain, no need to burden user with another photo
        if u_val <= self.target_max_unc and u_qual <= settings.MAX_QUALITY_UNCERTAINTY:
            return ControllerDecision(
                decision=ControllerAction.FINALIZE_VALUATION,
                reason=f"Valuation uncertainty ({u_val:.2f}) is below threshold ({self.target_max_unc:.2f}); confidence is sufficient.",
                current_uncertainty=u_val,
                expected_value_of_information=0.0,
                estimated_observation_cost=self.obs_cost,
                threshold=self.evi_threshold,
                observation_request=None,
            )

        # 3. Calculate Expected Value of Information (EVI)
        if current_observation_count == 1:
            expected_gain = settings.BASE_EXPECTED_GAIN_SECOND_VIEW
            next_view = "reverse_side"
            guidance = "Capture the other side of the produce to inspect hidden surfaces."
            request_reason = "Single-view observation leaves ~50% of produce surface occluded. Visual uncertainty is high."
        elif current_observation_count == 2:
            expected_gain = settings.BASE_EXPECTED_GAIN_THIRD_VIEW
            next_view = "close_up"
            guidance = "Capture a closer view focusing on any stem, bruising, or skin defects."
            request_reason = "Residual surface ambiguity detected. A targeted close-up can confirm condition."
        else:
            expected_gain = 0.05
            next_view = "overview"
            guidance = "Capture the entire item under even ambient lighting."
            request_reason = "General clarity check."

        expected_uncertainty_reduction = round(u_val * expected_gain, 3)
        evi = round(expected_uncertainty_reduction - self.obs_cost, 3)

        # 4. Trigger active observation if EVI exceeds threshold
        if evi > self.evi_threshold:
            obs_request = ObservationRequest(
                reason=request_reason,
                requested_view=next_view,
                priority=round(min(1.0, u_val * 1.2), 2),
                expected_information_gain=expected_gain,
                user_guidance=guidance,
            )
            return ControllerDecision(
                decision=ControllerAction.ACQUIRE_ADDITIONAL_OBSERVATION,
                reason=(
                    f"Expected Value of Information (EVI={evi:.3f}) exceeds threshold ({self.evi_threshold:.3f}). "
                    f"Additional observation expected to reduce uncertainty by ~{int(expected_uncertainty_reduction*100)}%."
                ),
                current_uncertainty=u_val,
                expected_value_of_information=evi,
                estimated_observation_cost=self.obs_cost,
                threshold=self.evi_threshold,
                observation_request=obs_request,
            )

        # 5. Fallback: Information gain does not justify observation cost
        return ControllerDecision(
            decision=ControllerAction.FINALIZE_VALUATION,
            reason=(
                f"Expected Value of Information (EVI={evi:.3f}) does not justify observation cost ({self.obs_cost:.3f}). "
                "Finalizing current valuation."
            ),
            current_uncertainty=u_val,
            expected_value_of_information=evi,
            estimated_observation_cost=self.obs_cost,
            threshold=self.evi_threshold,
            observation_request=None,
        )
