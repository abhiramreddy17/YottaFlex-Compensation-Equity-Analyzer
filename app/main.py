"""FastAPI service for compensation analysis."""
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from app.config import DATA_DIR
from app.compensation_engine import analyze_records
from app.anomaly_detector import detect_anomalies, create_review_proposals
from app.database import load_csv_tables

app = FastAPI(title="YottaFlex Compensation Equity Analyzer", version="1.0.0")

def read_data():
    required = ["employees.csv", "salary_records.csv", "compensation_bands.csv",
                "locations.csv", "adjustment_proposals.csv", "comparison_requests.csv"]
    missing = [x for x in required if not (DATA_DIR / x).exists()]
    if missing:
        raise HTTPException(503, f"Data missing: {missing}. Run the generator first.")
    return {name[:-4]: pd.read_csv(DATA_DIR / name) for name in required}

@app.get("/")
def root():
    return {"service": "YottaFlex Compensation Equity Analyzer", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/summary")
def summary():
    d = read_data()
    analysis = analyze_records(d["employees"], d["salary_records"], d["compensation_bands"], d["locations"])
    anomalies = detect_anomalies(d["employees"], d["salary_records"], d["compensation_bands"], d["adjustment_proposals"], analysis, d["comparison_requests"])
    return {"employees": int(d["employees"].shape[0]), "salary_records": int(d["salary_records"].shape[0]),
            "flagged_employees": int(anomalies.employee_id.nunique()) if not anomalies.empty else 0,
            "anomaly_count": int(len(anomalies)),
            "average_compa_ratio": round(float(analysis.compa_ratio.dropna().mean()), 3) if not analysis.empty else None}

@app.get("/employees/{employee_id}")
def employee_detail(employee_id: str):
    d = read_data()
    emp = d["employees"][d["employees"].employee_id.eq(employee_id)]
    if emp.empty:
        raise HTTPException(404, "Employee not found")
    records = d["salary_records"][d["salary_records"].employee_id.eq(employee_id)]
    return {"employee": emp.iloc[0].to_dict(), "salary_history": records.to_dict(orient="records")}

@app.get("/anomalies")
def anomalies():
    d = read_data()
    analysis = analyze_records(d["employees"], d["salary_records"], d["compensation_bands"], d["locations"])
    result = detect_anomalies(d["employees"], d["salary_records"], d["compensation_bands"], d["adjustment_proposals"], analysis, d["comparison_requests"])
    return result.astype(object).where(pd.notna(result), None).to_dict(orient="records")

@app.get("/review-proposals")
def review_proposals():
    d = read_data()
    analysis = analyze_records(d["employees"], d["salary_records"], d["compensation_bands"], d["locations"])
    findings = detect_anomalies(d["employees"], d["salary_records"], d["compensation_bands"], d["adjustment_proposals"], analysis, d["comparison_requests"])
    return create_review_proposals(analysis, findings).astype(object).where(pd.notna(create_review_proposals(analysis, findings)), None).to_dict(orient="records")

@app.post("/load-sqlite")
def load_sqlite():
    try:
        return {"loaded": load_csv_tables(DATA_DIR)}
    except Exception as exc:
        raise HTTPException(400, str(exc))
