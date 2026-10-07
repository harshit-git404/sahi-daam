# Ground-Truth Teardown Protocol

## Critical Architectural Invariant
**The controller NEVER reads hidden ground truth during inspection.**
Verified by unit test: `inspection_control/tests/test_planner_and_isolation.py::test_ground_truth_isolation_invariant` (PASSED).

## Post-Inspection Teardown Procedure
1. The controller terminates by issuing `PhysicalActionType.STOP_INSPECTION` and committing a terminal disposition.
2. The physical enclosure is fully opened.
3. Every unit across all strata is individually graded:
   - Defect presence (soft rot, internal browning, greening, scuff).
   - Defect severity index.
   - Stratum assignment.
4. Unbiased metrics calculated:
   - True lot defect prevalence vs estimated prevalence.
   - False Accept Rate ($	heta > 0.08$ accepted as premium).
   - False Reject Rate ($	heta \le 0.08$ dumped/rejected).
   - Economic disposition loss matrix evaluation (INR).
