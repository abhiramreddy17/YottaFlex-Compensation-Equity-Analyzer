"""Data quality and reproducibility validation."""
import pandas as pd

def validate_tables(tables):
    errors = []
    pk = {"employees": "employee_id", "roles": "role_id", "levels": "level_id",
          "locations": "location_id", "compensation_bands": "band_id",
          "salary_records": "salary_id", "performance_evidence": "evidence_id",
          "tenure": "tenure_id", "promotions": "promotion_id",
          "adjustment_proposals": "adjustment_id", "comparison_requests": "comparison_id"}
    for name, col in pk.items():
        df = tables.get(name, pd.DataFrame())
        if df.empty and name not in {"promotions", "adjustment_proposals"}:
            errors.append(f"{name}: unexpectedly empty")
        elif col in df and df[col].duplicated().any():
            errors.append(f"{name}: duplicate primary key {col}")
    emp_ids = set(tables["employees"].employee_id)
    role_ids, level_ids, loc_ids = set(tables["roles"].role_id), set(tables["levels"].level_id), set(tables["locations"].location_id)
    band_ids = set(tables["compensation_bands"].band_id)
    for _, r in tables["employees"].iterrows():
        if r.role_id not in role_ids or r.level_id not in level_ids or r.location_id not in loc_ids:
            errors.append(f"Employee {r.employee_id}: invalid master reference")
            break
    for _, r in tables["salary_records"].iterrows():
        if r.employee_id not in emp_ids or r.band_id not in band_ids:
            errors.append(f"Salary {r.salary_id}: invalid employee/band reference")
            break
        if str(r.effective_date) > str(r.end_date):
            errors.append(f"Salary {r.salary_id}: effective date after end date")
            break
    if "comparison_requests" in tables:
        for _, r in tables["comparison_requests"].iterrows():
            if r.employee_id_a not in emp_ids or r.employee_id_b not in emp_ids:
                errors.append(f"Comparison {r.comparison_id}: invalid employee reference")
                break
    if not tables["compensation_bands"].empty:
        b = tables["compensation_bands"]
        if ((b.min_salary > b.mid_salary) | (b.mid_salary > b.max_salary)).any():
            errors.append("Compensation band min/mid/max ordering invalid")
    return {"valid": len(errors) == 0, "errors": errors}

def checksums(directory):
    import hashlib
    from pathlib import Path
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(directory).glob("*.csv"))}
