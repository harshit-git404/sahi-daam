"""
inspection_control/evidence/logger.py
Immutable SQLite and CSV Audit Logging for Bulk Lot Inspection.
Records every decision step, environmental telemetry, and physical action.
"""

from typing import Dict, Any, Optional
import sqlite3
import csv
import json
import os
import time


class AuditLogger:
    """
    Structured ledger logging every action, sensor reading,
    planner score, and exposure state transition into SQLite and CSV.
    """

    def __init__(
        self,
        db_path: str = "evidence/inspection_audit.db",
        csv_path: str = "evidence/audit_log.csv",
    ):
        self.db_path = db_path
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_sqlite()
        self._init_csv()

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspection_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    lot_id TEXT,
                    step_index INTEGER,
                    stratum_id INTEGER,
                    action TEXT,
                    operator_status TEXT,
                    core_temp_c REAL,
                    ambient_temp_c REAL,
                    rh_pct REAL,
                    cumulative_exposure_sec REAL,
                    observation_quality REAL,
                    defect_probability REAL,
                    confidence REAL,
                    planner_score REAL,
                    chosen_action TEXT,
                    reason TEXT,
                    final_disposition TEXT,
                    metadata_json TEXT
                )
            """)
            conn.commit()

    def _init_csv(self) -> None:
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "lot_id", "step_index", "stratum_id", "action",
                    "operator_status", "core_temp_c", "ambient_temp_c", "rh_pct",
                    "cumulative_exposure_sec", "observation_quality", "defect_probability",
                    "confidence", "planner_score", "chosen_action", "reason",
                    "final_disposition"
                ])

    def log_step(
        self,
        lot_id: str,
        step_index: int,
        stratum_id: int,
        action: str,
        operator_status: str,
        core_temp_c: float,
        ambient_temp_c: float,
        rh_pct: float,
        cumulative_exposure_sec: float,
        observation_quality: Optional[float] = None,
        defect_probability: Optional[float] = None,
        confidence: Optional[float] = None,
        planner_score: Optional[float] = None,
        chosen_action: Optional[str] = None,
        reason: Optional[str] = None,
        final_disposition: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        ts = time.time()
        meta_str = json.dumps(metadata or {})

        # Write to SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspection_steps (
                    timestamp, lot_id, step_index, stratum_id, action,
                    operator_status, core_temp_c, ambient_temp_c, rh_pct,
                    cumulative_exposure_sec, observation_quality, defect_probability,
                    confidence, planner_score, chosen_action, reason,
                    final_disposition, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts, lot_id, step_index, stratum_id, action,
                operator_status, core_temp_c, ambient_temp_c, rh_pct,
                cumulative_exposure_sec, observation_quality, defect_probability,
                confidence, planner_score, chosen_action, reason,
                final_disposition, meta_str
            ))
            conn.commit()

        # Write to CSV
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts, lot_id, step_index, stratum_id, action,
                operator_status, core_temp_c, ambient_temp_c, rh_pct,
                cumulative_exposure_sec, observation_quality, defect_probability,
                confidence, planner_score, chosen_action, reason,
                final_disposition
            ])
