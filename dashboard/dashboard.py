"""Streamlit dashboard. Run with: streamlit run dashboard/dashboard.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import streamlit as st
import plotly.express as px
from app.config import DATA_DIR
from app.compensation_engine import analyze_records
from app.anomaly_detector import detect_anomalies, create_review_proposals

st.set_page_config(page_title="Compensation Equity Analyzer", layout="wide")
st.title("Employee Compensation Equity Analyzer")
st.caption("Synthetic demonstration data | Rule-based decision support | HR review required")
required = ["employees", "salary_records", "compensation_bands", "locations", "adjustment_proposals", "comparison_requests"]
missing = [n for n in required if not (DATA_DIR / f"{n}.csv").exists()]
if missing:
    st.error(f"Missing data files: {missing}. Run `python -m app.data_generator` from project root.")
    st.stop()
d = {n: pd.read_csv(DATA_DIR / f"{n}.csv") for n in required}
analysis = analyze_records(d["employees"], d["salary_records"], d["compensation_bands"], d["locations"])
findings = detect_anomalies(d["employees"], d["salary_records"], d["compensation_bands"], d["adjustment_proposals"], analysis, d["comparison_requests"])
proposals = create_review_proposals(analysis, findings)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Employees", f"{len(d['employees']):,}")
c2.metric("Salary records", f"{len(d['salary_records']):,}")
c3.metric("Employees flagged", f"{findings.employee_id.nunique() if not findings.empty else 0:,}")
c4.metric("Average compa-ratio", f"{analysis.compa_ratio.dropna().mean():.2f}" if analysis.compa_ratio.notna().any() else "N/A")
st.subheader("Compensation distribution")
valid = analysis.dropna(subset=["normalized_salary_inr", "role_id"])
if not valid.empty:
    fig = px.box(valid, x="level_id", y="normalized_salary_inr", color="city",
                 title="Normalized annual FTE salary by level and location")
    st.plotly_chart(fig, use_container_width=True)
left,right = st.columns(2)
with left:
    st.subheader("Anomaly types")
    if findings.empty:
        st.info("No anomalies detected.")
    else:
        counts = findings.issue_type.value_counts().rename_axis("issue_type").reset_index(name="count")
        st.plotly_chart(px.bar(counts, x="issue_type", y="count"), use_container_width=True)
with right:
    st.subheader("Compa-ratio distribution")
    ratios = analysis.dropna(subset=["compa_ratio"])
    if not ratios.empty:
        st.plotly_chart(px.histogram(ratios, x="compa_ratio", nbins=30), use_container_width=True)
st.subheader("HR review queue")
if proposals.empty:
    st.info("No review proposals.")
else:
    st.dataframe(proposals, use_container_width=True)
st.subheader("Anomaly evidence")
st.dataframe(findings, use_container_width=True)
st.subheader("Employee lookup")
employee_id = st.text_input("Employee ID", value="EMP-000001")
if employee_id:
    emp = analysis[analysis.employee_id.eq(employee_id)]
    if emp.empty:
        st.warning("No current analysis record found.")
    else:
        st.dataframe(emp, use_container_width=True)
st.download_button("Download anomaly report CSV", findings.to_csv(index=False), "anomaly_report.csv", "text/csv")
