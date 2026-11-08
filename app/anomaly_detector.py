"""Rule-based anomaly detection. Ground-truth labels are never read here."""
import pandas as pd
from app.config import AS_OF_DATE

def detect_anomalies(employees, salaries, bands, proposals, analysis=None, comparison_requests=None):
    findings = []
    emp_map = employees.set_index("employee_id").to_dict("index") if not employees.empty else {}
    band_map = bands.set_index("band_id").to_dict("index") if not bands.empty else {}
    # Evaluate the latest salary snapshot for each employee; older salary rows are
    # retained as history and must not be treated as current exceptions.
    current_salaries = (salaries.sort_values("effective_date").groupby("employee_id", as_index=False).tail(1)
                        if not salaries.empty else salaries)
    for _, s in current_salaries.iterrows():
        emp = emp_map.get(s.employee_id, {})
        band = band_map.get(s.band_id, {})
        if not emp or not band:
            findings.append({"employee_id": s.employee_id, "issue_type": "INVALID_REFERENCE",
                             "severity": "HIGH", "explanation": "Employee or compensation band reference is missing."})
            continue
        if str(band.get("effective_start", "")) > AS_OF_DATE or str(band.get("effective_end", "")) < AS_OF_DATE:
            findings.append({"employee_id": s.employee_id, "issue_type": "EXPIRED_BAND",
                             "severity": "HIGH", "explanation": "Salary record or linked band is not effective on review date."})
        if abs(float(s.fte_at_record) - float(emp.get("fte", 1))) > 0.001:
            findings.append({"employee_id": s.employee_id, "issue_type": "FTE_IGNORED",
                             "severity": "MEDIUM", "explanation": "Salary record FTE differs from employee master FTE."})
        if s.currency not in {"INR", "USD", "GBP"}:
            findings.append({"employee_id": s.employee_id, "issue_type": "MISSING_FX",
                             "severity": "HIGH", "explanation": f"No configured exchange rate for currency {s.currency}."})
    if not proposals.empty:
        for _, p in proposals.iterrows():
            if str(p.status).upper() == "APPLIED" and (pd.isna(p.approved_by) or not str(p.approved_by).strip()):
                findings.append({"employee_id": p.employee_id, "issue_type": "UNAPPROVED_ADJUSTMENT",
                                 "severity": "CRITICAL", "explanation": "Adjustment is marked APPLIED without an approver."})
    if analysis is not None and not analysis.empty:
        # Contextual salary band outliers. FTE/currency failures are excluded from numeric judgement.
        for _, r in analysis.iterrows():
            if pd.notna(r.get("normalized_salary_inr")) and pd.notna(r.get("band_min_inr")):
                if r.normalized_salary_inr < r.band_min_inr or r.normalized_salary_inr > r.band_max_inr:
                    findings.append({"employee_id": r.employee_id, "issue_type": "OUTSIDE_BAND",
                                     "severity": "MEDIUM", "explanation": "Normalized FTE salary is outside the effective compensation band."})
    if comparison_requests is not None and not comparison_requests.empty:
        employee_map = employees.set_index("employee_id").to_dict("index")
        for _, request in comparison_requests.iterrows():
            a = employee_map.get(request.employee_id_a, {})
            b = employee_map.get(request.employee_id_b, {})
            same_group = bool(a and b and a.get("role_id") == b.get("role_id")
                              and a.get("level_id") == b.get("level_id")
                              and a.get("location_id") == b.get("location_id"))
            if not same_group and not str(request.get("rationale", "")).strip():
                findings.append({"employee_id": request.employee_id_a, "issue_type": "INCOMPARABLE_GROUP",
                                 "severity": "HIGH", "explanation": "Comparison request mixes role/level/location groups without documented rationale."})
    # De-duplicate same employee/type while preserving deterministic order.
    result = pd.DataFrame(findings)
    if not result.empty:
        result = result.drop_duplicates(["employee_id", "issue_type"]).sort_values(["severity", "employee_id"])
    return result.reset_index(drop=True)

def create_review_proposals(analysis, anomalies):
    """Create review recommendations only; never automatically change payroll."""
    if analysis.empty:
        return pd.DataFrame()
    flagged = set(anomalies.employee_id) if not anomalies.empty else set()
    rows = []
    for _, r in analysis.iterrows():
        if r.employee_id in flagged:
            rows.append({"proposal_id": f"REVIEW-{r.employee_id}", "employee_id": r.employee_id,
                         "current_salary_inr": r.normalized_salary_inr,
                         "compa_ratio": r.compa_ratio, "status": "PENDING_HR_REVIEW",
                         "recommendation": "Investigate evidence and effective-dated band before any adjustment."})
    return pd.DataFrame(rows)
