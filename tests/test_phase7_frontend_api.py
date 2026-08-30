import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestPhase7FrontendAPI:
    def test_kpi_overview_endpoint(self, client):
        """
        Verify GET /api/kpi/overview returns all 5 standard KPIs,
        prioritizing the most material movement.
        """
        response = client.get("/api/kpi/overview?scenario_id=SCENARIO_1_MULTI_FACTOR")
        assert response.status_code == 200
        data = response.json()
        assert "scenario_id" in data
        assert data["scenario_id"] == "SCENARIO_1_MULTI_FACTOR"
        assert "kpis" in data
        kpis = data["kpis"]
        assert len(kpis) == 5
        
        # Verify required properties on each KPI card
        for k in kpis:
            assert "kpi_id" in k
            assert "name" in k
            assert "current_value" in k
            assert "baseline_value" in k
            assert "percentage_change" in k
            assert "business_materiality" in k
            assert "overall_materiality" in k
            assert "direction" in k
        
        # Top KPI in SCENARIO_1_MULTI_FACTOR should be kpi_revenue (highest percentage drop)
        assert kpis[0]["kpi_id"] == "kpi_revenue"
        assert kpis[0]["business_materiality"] == "MATERIAL"
        assert kpis[0]["overall_materiality"] == "CRITICAL_ACTIONABLE"

    def test_feedback_submission_endpoint(self, client):
        """
        Verify POST /api/feedback/submit stores analyst ratings into evaluation registry.
        """
        payload = {
            "request_id": "REQ-TEST-12345",
            "kpi_id": "kpi_revenue",
            "scenario_id": "SCENARIO_1_MULTI_FACTOR",
            "persona": "EXECUTIVE",
            "user_role": "ANALYST",
            "rating": "CORRECT",
            "feedback_text": "Decomposition perfectly aligns with EU payment gateway incident.",
            "corrected_driver": None
        }
        res = client.post("/api/feedback/submit", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "record" in data
        rec = data["record"]
        assert rec["feedback_id"].startswith("FB-")
        assert rec["rating"] == "CORRECT"
        assert rec["status"] == "STORED_FOR_EVALUATION"

    def test_feedback_list_endpoint(self, client):
        """
        Verify GET /api/feedback/list returns logged feedback records.
        """
        res = client.get("/api/feedback/list")
        assert res.status_code == 200
        logs = res.json()
        assert isinstance(logs, list)
        assert len(logs) >= 1

    def test_all_scenarios_overview_support(self, client):
        """
        Verify /api/kpi/overview generates complete KPI rankings for all 5 demo scenarios.
        """
        scenarios = [
            "SCENARIO_1_MULTI_FACTOR",
            "SCENARIO_2_HIGH_CONFIDENCE",
            "SCENARIO_3_LOW_CONFIDENCE",
            "SCENARIO_4_SPARSE_HISTORY",
            "SCENARIO_5_CONTRADICTORY_EVIDENCE"
        ]
        for sc in scenarios:
            res = client.get(f"/api/kpi/overview?scenario_id={sc}")
            assert res.status_code == 200
            data = res.json()
            assert len(data.get("kpis", [])) == 5
