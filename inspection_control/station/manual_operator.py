"""
inspection_control/station/manual_operator.py
Interactive manual operator workflow adapter for human-assisted physical inspection.
"""

from typing import Dict, Any, Optional
import time

from inspection_control.domain.access_graph import AccessAction, PhysicalActionType


class ManualOperatorInterface:
    """
    Dispatches human-readable instructions to an on-site warehouse operator
    and logs execution confirmations, skips, and manual overrides.
    """

    def __init__(self, auto_confirm: bool = True):
        self.auto_confirm = auto_confirm
        self.action_log = []

    def dispatch_instruction(self, action: AccessAction) -> Dict[str, Any]:
        """Format clean physical instructions for the operator."""
        if action.action_type == PhysicalActionType.REMOVE_LAYER:
            instruction = f"ACTION REQUIRED: REMOVE TRAY {action.target_stratum_id - 1} TO UNCOVER STRATUM {action.target_stratum_id}"
        elif action.action_type == PhysicalActionType.OPEN_STRATUM:
            instruction = f"ACTION REQUIRED: OPEN AND EXPOSE STRATUM {action.target_stratum_id}"
        elif action.action_type == PhysicalActionType.OBSERVE_STRATUM:
            instruction = f"ACTION REQUIRED: POSITION RGB SENSOR OVER STRATUM {action.target_stratum_id}"
        elif action.action_type == PhysicalActionType.SAMPLE_UNITS:
            instruction = f"ACTION REQUIRED: EXTRACT 3 CORE SAMPLE UNITS FROM STRATUM {action.target_stratum_id} FOR BRIX/FIRMNESS"
        elif action.action_type == PhysicalActionType.CLOSE_REDUCE_EXPOSURE:
            instruction = "ACTION REQUIRED: PLACE THERMAL COVER OVER OPEN LOT TO PREVENT WARMING"
        elif action.action_type == PhysicalActionType.WAIT_SETTLE:
            instruction = "ACTION REQUIRED: WAIT 10 SECONDS FOR DUST AND VIBRATION TO SETTLE"
        elif action.action_type == PhysicalActionType.STOP_INSPECTION:
            instruction = "INSPECTION COMPLETE: SEAL LOT AND PROCEED TO DISPOSITION"
        else:
            instruction = f"ACTION: {action.name}"

        event = {
            "timestamp": time.time(),
            "action_type": action.action_type.value,
            "target_stratum": action.target_stratum_id,
            "instruction_text": instruction,
            "operator_status": "CONFIRMED" if self.auto_confirm else "PENDING_CONFIRMATION",
        }
        self.action_log.append(event)
        return event

    def confirm_action_completed(self, override_comment: Optional[str] = None) -> Dict[str, Any]:
        if not self.action_log:
            return {"status": "NO_ACTIVE_INSTRUCTION"}
        
        last = self.action_log[-1]
        last["operator_status"] = "OVERRIDDEN" if override_comment else "CONFIRMED"
        last["override_comment"] = override_comment
        last["confirmation_timestamp"] = time.time()
        return last
