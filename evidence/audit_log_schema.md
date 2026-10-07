# Audit Log Database Schema (`inspection_audit.db` & `audit_log.csv`)

Every single decision, sensor capture, and physical actuation is logged immutably:

| Column | Type | Description |
|---|---|---|
| `timestamp` | REAL | Epoch timestamp (seconds) |
| `lot_id` | TEXT | Unique lot tracking ID |
| `step_index` | INTEGER | Sequential step in inspection episode |
| `stratum_id` | INTEGER | Target stratum index (0..4) |
| `action` | TEXT | Physical action name |
| `operator_status` | TEXT | CONFIRMED / EXECUTED / OVERRIDDEN / STOPPED |
| `core_temp_c` | REAL | Measured produce core temperature (°C) |
| `ambient_temp_c` | REAL | Measured warehouse ambient temperature (°C) |
| `rh_pct` | REAL | Ambient relative humidity (%) |
| `cumulative_exposure_sec` | REAL | Non-additive cumulative exposure time for target stratum |
| `observation_quality` | REAL | Visual quality score [0, 1] |
| `defect_probability` | REAL | Estimated defect fraction [0, 1] |
| `confidence` | REAL | Sensor confidence score after exposure attenuation |
| `planner_score` | REAL | Expected net economic benefit (INR) |
| `chosen_action` | TEXT | Selected candidate action |
| `reason` | TEXT | Decision rationale string |
| `final_disposition` | TEXT | Terminal decision (ACCEPT, MARKDOWN, REJECT, REROUTE, SPLIT) |
