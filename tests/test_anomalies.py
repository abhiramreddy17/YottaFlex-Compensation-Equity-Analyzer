import pandas as pd
from app.anomaly_detector import detect_anomalies

def test_unapproved_applied_adjustment_detected():
    employees = pd.DataFrame([{"employee_id":"EMP-000001","fte":1.0}])
    salaries = pd.DataFrame(columns=["employee_id","band_id","end_date","fte_at_record","currency"])
    bands = pd.DataFrame(columns=["band_id","effective_end"])
    proposals = pd.DataFrame([{"employee_id":"EMP-000001","status":"APPLIED","approved_by":""}])
    result = detect_anomalies(employees, salaries, bands, proposals)
    assert "UNAPPROVED_ADJUSTMENT" in set(result.issue_type)
