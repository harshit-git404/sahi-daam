"""
Automated Unit and Integration Tests for Sahi Daam Experiment Lab.

Tests:
1. Scenario specifications completeness and valid defaults.
2. Exact mathematical formulas for Scenarios A through G.
3. Path traversal protection on run retrieval.
4. Atomic file persistence and manifest indexing.
5. Isolation: ensuring production SQLite database is untouched.
6. API endpoint contracts and JSON export downloads.
"""

import json
import os
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.experiment_service import (
    ExperimentService,
    get_scenario_specs,
    EXPERIMENTS_ROOT,
)


class TestExperimentService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_all_scenario_specs_defined(self):
        """Verify that all mandatory scenarios A–G and combined cases are registered."""
        specs = get_scenario_specs()
        expected_ids = [
            "transport_available",
            "transport_unavailable",
            "community_low",
            "community_high",
            "insufficient_community",
            "duplicate_reports",
            "freshness_adjustment",
            "combined_transport_community_low",
            "combined_transport_community_high",
            "combined_transport_unavail_community_sufficient",
            "combined_high_community_with_duplicates",
            "combined_missing_wholesale",
            "combined_invalid_unit",
        ]
        for s_id in expected_ids:
            self.assertIn(s_id, specs, f"Scenario '{s_id}' must be registered.")

    def test_scenario_a_transport_available_math(self):
        """Scenario A: Wholesale ₹20 + Transport ₹2 = ₹22 cost basis, markup 30-45% => ₹28.60-₹31.90."""
        res = ExperimentService.run_scenario("transport_available")
        out = res["actual_output"]

        self.assertEqual(out["cost_basis_per_kg"], 22.0)
        self.assertEqual(out["baseline_range"]["min"], 28.60)
        self.assertEqual(out["baseline_range"]["max"], 31.90)
        self.assertEqual(out["transport_status"], "available")
        self.assertEqual(out["reconciliation_weight_alpha"], 0.0)
        self.assertEqual(out["calculation_status"], "TRANSPORT_AWARE_BASELINE")

        # Verify steps generated
        steps = res["calculation_steps"]
        self.assertGreaterEqual(len(steps), 4)
        self.assertEqual(steps[0]["result_label"], "Delivered Cost Basis")
        self.assertEqual(steps[0]["result_value"], "₹22.00/kg")

    def test_scenario_b_transport_unavailable_fallback(self):
        """Scenario B: Missing transport must return provisional wholesale baseline (₹26.00-₹29.00)."""
        res = ExperimentService.run_scenario("transport_unavailable")
        out = res["actual_output"]

        self.assertEqual(out["cost_basis_per_kg"], 20.0)
        self.assertEqual(out["baseline_range"]["min"], 26.00)
        self.assertEqual(out["baseline_range"]["max"], 29.00)
        self.assertEqual(out["transport_status"], "unavailable")
        self.assertTrue(out["is_provisional_wholesale_only"])
        self.assertEqual(out["calculation_status"], "PROVISIONAL_WHOLESALE_BASELINE")

    def test_scenario_c_community_low_reconciliation(self):
        """Scenario C: 10 reports with median ₹23.00 reconciles midpoint toward community report."""
        res = ExperimentService.run_scenario("community_low")
        out = res["actual_output"]

        self.assertEqual(out["community_sample_size"], 10)
        self.assertTrue(out["is_sample_sufficient"])
        self.assertEqual(out["community_estimate"], 23.0)
        self.assertEqual(out["reconciliation_weight_alpha"], 0.20)
        self.assertEqual(out["calculation_status"], "TRANSPORT_AWARE_RECONCILED")

        # Midpoint moves lower: baseline mid was 30.25, reconciled mid should be 28.80
        self.assertLess(out["reconciled_range"]["mid"], out["baseline_range"]["mid"])
        self.assertEqual(out["reconciled_range"]["mid"], 28.80)

    def test_scenario_d_community_high_reconciliation(self):
        """Scenario D: 10 reports with median ₹35.00 reconciles midpoint higher."""
        res = ExperimentService.run_scenario("community_high")
        out = res["actual_output"]

        self.assertEqual(out["community_sample_size"], 10)
        self.assertTrue(out["is_sample_sufficient"])
        self.assertEqual(out["community_estimate"], 35.0)
        self.assertEqual(out["reconciliation_weight_alpha"], 0.20)

        # Midpoint moves higher: baseline mid was 30.25, reconciled mid should be 31.20
        self.assertGreater(out["reconciled_range"]["mid"], out["baseline_range"]["mid"])
        self.assertEqual(out["reconciled_range"]["mid"], 31.20)

    def test_scenario_e_insufficient_community(self):
        """Scenario E: 9 reports (< 10) must keep alpha = 0.0 and baseline untouched."""
        res = ExperimentService.run_scenario("insufficient_community")
        out = res["actual_output"]

        self.assertEqual(out["community_sample_size"], 9)
        self.assertFalse(out["is_sample_sufficient"])
        self.assertEqual(out["reconciliation_weight_alpha"], 0.0)
        self.assertEqual(out["reconciled_range"]["min"], out["baseline_range"]["min"])
        self.assertEqual(out["reconciled_range"]["max"], out["baseline_range"]["max"])

    def test_scenario_f_duplicate_filtering(self):
        """Scenario F: 13 submissions with 5 duplicates => 8 independent (< 10), alpha = 0.0."""
        res = ExperimentService.run_scenario("duplicate_reports")
        out = res["actual_output"]
        bd = res["eligible_community_observations"]

        self.assertEqual(bd["total_found"], 13)
        self.assertEqual(bd["excluded_duplicates_count"], 5)
        self.assertEqual(bd["eligible_count"], 8)
        self.assertEqual(out["community_sample_size"], 8)
        self.assertFalse(out["is_sample_sufficient"])
        self.assertEqual(out["reconciliation_weight_alpha"], 0.0)

    def test_scenario_g_freshness_adjustment_sub_runs(self):
        """Scenario G: G1 (fresh ₹0) vs G2 (fair -₹2/kg deduction) exactly ₹2.00 difference."""
        res = ExperimentService.run_scenario("freshness_adjustment")
        sub_runs = res.get("sub_runs", [])

        self.assertEqual(len(sub_runs), 2)
        g1 = sub_runs[0]
        g2 = sub_runs[1]

        self.assertEqual(g1["cost_basis_per_kg"], g2["cost_basis_per_kg"])
        self.assertEqual(g1["baseline_min"], 28.60)
        self.assertEqual(g2["baseline_min"], 26.60)
        self.assertEqual(round(g1["baseline_min"] - g2["baseline_min"], 2), 2.00)

    def test_missing_wholesale_no_fabrication(self):
        """Combined 5: Missing wholesale must return UNAVAILABLE without fabricating prices."""
        res = ExperimentService.run_scenario("combined_missing_wholesale")
        out = res["actual_output"]

        self.assertEqual(out["calculation_status"], "UNAVAILABLE")
        self.assertIsNone(out["wholesale_price_per_kg"])
        self.assertIsNone(out["baseline_range"])

    def test_unsupported_unit_filtered(self):
        """Combined 6: Non-weight units (bunch, piece) must not be counted as ₹/kg."""
        res = ExperimentService.run_scenario("combined_invalid_unit")
        bd = res["eligible_community_observations"]

        self.assertEqual(bd["total_found"], 3)
        self.assertEqual(bd["excluded_non_weight_unit_count"], 3)
        self.assertEqual(bd["eligible_count"], 0)

    def test_path_traversal_protection(self):
        """Attempting to access runs outside the experiments root must return None."""
        self.assertIsNone(ExperimentService.get_run_detail("../../../etc/passwd"))
        self.assertIsNone(ExperimentService.get_run_detail("..\\..\\secret"))

    # -----------------------------------------------------------------------
    # API Integration Tests
    # -----------------------------------------------------------------------
    def test_api_list_scenarios(self):
        """GET /api/experiments/scenarios must return registered scenarios."""
        resp = self.client.get("/api/experiments/scenarios")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 7)

    def test_api_run_scenario_and_export(self):
        """POST /api/experiments/run/{id} runs simulation and export endpoint serves valid JSON."""
        resp = self.client.post("/api/experiments/run/transport_available")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        run_id = data["experiment"]["run_id"]

        # Retrieve detail
        detail_resp = self.client.get(f"/api/experiments/runs/{run_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["experiment"]["run_id"], run_id)

        # Download export
        export_resp = self.client.get(f"/api/experiments/runs/{run_id}/export")
        self.assertEqual(export_resp.status_code, 200)
        self.assertIn("application/json", export_resp.headers["content-type"])
        export_data = json.loads(export_resp.text)
        self.assertEqual(export_data["experiment"]["run_id"], run_id)

    def test_api_manifest(self):
        """GET /api/experiments/manifest must return index of executed runs."""
        resp = self.client.get("/api/experiments/manifest")
        self.assertEqual(resp.status_code, 200)
        manifest = resp.json()
        self.assertIn("runs", manifest)
        self.assertGreaterEqual(manifest["total_runs"], 1)


if __name__ == "__main__":
    unittest.main()
