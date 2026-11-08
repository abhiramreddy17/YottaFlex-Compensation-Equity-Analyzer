"""Deterministic synthetic HR compensation data generator.

The generator creates master data first, then dependent records. Ground truth is
written separately and is never joined into model/detection input features.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from app.config import DATA_DIR, GROUND_TRUTH_DIR, SEED

ROLES = [
    "Software Engineer", "Python Developer", "Data Analyst", "Data Engineer",
    "QA Engineer", "Embedded Engineer", "DevOps Engineer", "Product Analyst",
    "Business Analyst", "ML Engineer"
]
LEVELS = ["L1", "L2", "L3", "L4"]
LOCATIONS = [
    ("Hyderabad", "INR", 1.00), ("Bengaluru", "INR", 1.08),
    ("Pune", "INR", 0.96), ("Chennai", "INR", 0.98),
    ("London", "GBP", 1.35), ("New York", "USD", 1.55)
]
CURRENCY_TO_INR = {"INR": 1.0, "USD": 83.0, "GBP": 105.0}
LEVEL_FACTOR = {"L1": 1.0, "L2": 1.35, "L3": 1.8, "L4": 2.35}
ROLE_FACTOR = {r: 1.0 + i * 0.025 for i, r in enumerate(ROLES)}

def _id(prefix: str, n: int, width: int = 6) -> str:
    return f"{prefix}-{n:0{width}d}"

def generate_dataset(n_employees: int = 5000, seed: int = SEED,
                     output_dir: Path = DATA_DIR, truth_dir: Path = GROUND_TRUTH_DIR):
    if n_employees < 1:
        raise ValueError("n_employees must be at least 1")
    rng = np.random.default_rng(seed)
    output_dir, truth_dir = Path(output_dir), Path(truth_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)

    # 1. Master data
    roles = pd.DataFrame([{"role_id": f"ROLE-{i+1:03d}", "role_name": r}
                          for i, r in enumerate(ROLES)])
    levels = pd.DataFrame([{"level_id": f"LVL-{i+1:02d}", "level_name": l,
                            "level_order": i+1} for i, l in enumerate(LEVELS)])
    locations = pd.DataFrame([{"location_id": f"LOC-{i+1:03d}", "city": x[0],
                               "currency": x[1], "location_factor": x[2]}
                              for i, x in enumerate(LOCATIONS)])

    bands = []
    band_lookup = {}
    band_no = 1
    for role in ROLES:
        for level in LEVELS:
            for city, currency, loc_factor in LOCATIONS:
                midpoint_inr = 420000 * ROLE_FACTOR[role] * LEVEL_FACTOR[level] * loc_factor
                fx = CURRENCY_TO_INR[currency]
                low, mid, high = midpoint_inr * 0.80 / fx, midpoint_inr / fx, midpoint_inr * 1.20 / fx
                bid = f"BAND-{role.replace(' ', '').upper()}-{level}-{city.upper()}-2026"
                rec = {"band_id": bid, "role_id": roles.loc[roles.role_name.eq(role), "role_id"].iloc[0],
                       "level_id": levels.loc[levels.level_name.eq(level), "level_id"].iloc[0],
                       "location_id": locations.loc[locations.city.eq(city), "location_id"].iloc[0],
                       "currency": currency, "min_salary": round(low, 2),
                       "mid_salary": round(mid, 2), "max_salary": round(high, 2),
                       "effective_start": "2026-01-01", "effective_end": "2026-12-31",
                       "status": "ACTIVE"}
                bands.append(rec)
                band_lookup[(role, level, city)] = rec
                band_no += 1
    bands = pd.DataFrame(bands)

    # 2. Employees and dependent transactions
    employees, salaries, performance, tenures, promotions, proposals = [], [], [], [], [], []
    truth = []
    start = pd.Timestamp("2023-01-01")
    end = pd.Timestamp("2026-11-06")
    for i in range(1, n_employees + 1):
        role = ROLES[int(rng.integers(0, len(ROLES)))]
        level_idx = int(rng.integers(0, len(LEVELS)))
        level = LEVELS[level_idx]
        city, currency, _ = LOCATIONS[int(rng.integers(0, len(LOCATIONS)))]
        employee_id = _id("EMP", i)
        join_date = start + pd.Timedelta(days=int(rng.integers(0, 1000)))
        fte = float(rng.choice([1.0, 1.0, 1.0, 0.75, 0.5]))
        employees.append({
            "employee_id": employee_id, "employee_name": f"Employee {i:06d}",
            "role_id": roles.loc[roles.role_name.eq(role), "role_id"].iloc[0],
            "level_id": levels.loc[levels.level_name.eq(level), "level_id"].iloc[0],
            "location_id": locations.loc[locations.city.eq(city), "location_id"].iloc[0],
            "joining_date": join_date.date().isoformat(), "employment_status": "ACTIVE",
            "fte": fte
        })
        band = band_lookup[(role, level, city)]
        base_in_currency = band["mid_salary"] * float(rng.normal(0.98, 0.09)) * fte
        base_in_currency = max(band["min_salary"] * fte * 0.75, base_in_currency)
        for year in (2024, 2025, 2026):
            effective = pd.Timestamp(year=year, month=1, day=1)
            if effective < join_date:
                continue
            # Modest annual merit movement, deterministic for seed.
            salary = base_in_currency * (1 + 0.04 * (year - 2024))
            # A documented promotion changes level in later year for some employees.
            if year == 2026 and level_idx < 3 and i % 17 == 0:
                new_level = LEVELS[level_idx + 1]
                new_band = band_lookup[(role, new_level, city)]
                salary = new_band["mid_salary"] * fte * float(rng.uniform(0.88, 1.04))
                promotions.append({"promotion_id": f"PROM-{i:06d}-2026", "employee_id": employee_id,
                                   "from_level_id": employees[-1]["level_id"],
                                   "to_level_id": levels.loc[levels.level_name.eq(new_level), "level_id"].iloc[0],
                                   "effective_date": "2026-01-01", "reason": "Annual progression"})
                employees[-1]["level_id"] = levels.loc[levels.level_name.eq(new_level), "level_id"].iloc[0]
                level = new_level
                band = new_band
            # A few FX changes are represented by the employee's current location/currency.
            salary_id = f"SAL-{employee_id}-{year}-01"
            salaries.append({"salary_id": salary_id, "employee_id": employee_id,
                             "band_id": band["band_id"], "effective_date": effective.date().isoformat(),
                             "end_date": f"{year}-12-31", "base_salary": round(salary, 2),
                             "currency": currency, "fte_at_record": fte,
                             "annualized": True, "source": "SYNTHETIC_PAYROLL"})
        rating = int(rng.choice([2, 3, 3, 3, 4, 5]))
        performance.append({"evidence_id": f"PERF-{i:06d}-2026", "employee_id": employee_id,
                            "review_period": "2025", "rating": rating,
                            "evidence_note": "Synthetic annual performance rating"})
        tenures.append({"tenure_id": f"TEN-{i:06d}", "employee_id": employee_id,
                        "start_date": join_date.date().isoformat(),
                        "years_of_service": round((end - join_date).days / 365.25, 2)})

    employees = pd.DataFrame(employees)
    salaries = pd.DataFrame(salaries)
    performance = pd.DataFrame(performance)
    tenures = pd.DataFrame(tenures)
    promotions = pd.DataFrame(promotions, columns=["promotion_id","employee_id","from_level_id","to_level_id","effective_date","reason"])

    # 3. Deliberate labelled edge cases, applied only to existing records.
    issue_types = ["EXPIRED_BAND", "FTE_IGNORED", "MISSING_FX", "UNAPPROVED_ADJUSTMENT", "INCOMPARABLE_GROUP"]
    selected = [min(n_employees - 1, max(0, int(n_employees * p))) for p in (0.05, 0.10, 0.15, 0.20, 0.25)]
    for j, idx in enumerate(selected):
        emp = employees.iloc[idx]
        emp_id = emp.employee_id
        if salaries.empty:
            continue
        rows = salaries.index[salaries.employee_id.eq(emp_id)].tolist()
        if not rows:
            continue
        sidx = rows[-1]
        if j == 0:
            # Expire the referenced band, not the salary record: salary dates remain internally valid.
            expired_band_id = salaries.loc[sidx, "band_id"]
            bands.loc[bands.band_id.eq(expired_band_id), "effective_end"] = "2025-12-31"
            bands.loc[bands.band_id.eq(expired_band_id), "status"] = "EXPIRED"
            truth.append({"employee_id": emp_id, "issue_type": "EXPIRED_BAND",
                          "expected_decision": "FLAG_EXPIRED_BAND", "reason": "Salary record points to a band not effective on the review date."})
        elif j == 1:
            if float(emp.fte) < 1:
                salaries.loc[sidx, "fte_at_record"] = 1.0
            else:
                employees.loc[employees.employee_id.eq(emp_id), "fte"] = 0.5
                salaries.loc[sidx, "fte_at_record"] = 1.0
            truth.append({"employee_id": emp_id, "issue_type": "FTE_IGNORED",
                          "expected_decision": "FLAG_FTE_MISMATCH", "reason": "Recorded FTE differs from employee FTE."})
        elif j == 2:
            salaries.loc[sidx, "currency"] = "XYZ"
            truth.append({"employee_id": emp_id, "issue_type": "MISSING_FX",
                          "expected_decision": "FLAG_MISSING_FX", "reason": "No conversion rate exists for currency XYZ."})
        elif j == 3:
            proposals.append({"adjustment_id": f"ADJ-2026-{len(proposals)+1:06d}",
                              "employee_id": emp_id, "proposed_salary": 999999,
                              "currency": "INR", "status": "APPLIED",
                              "created_date": "2026-06-01", "approved_by": "",
                              "reason": "Synthetic deliberately unapproved adjustment"})
            truth.append({"employee_id": emp_id, "issue_type": "UNAPPROVED_ADJUSTMENT",
                          "expected_decision": "FLAG_UNAPPROVED_APPLIED_ADJUSTMENT", "reason": "Applied adjustment has no approval record."})
        else:
            truth.append({"employee_id": emp_id, "issue_type": "INCOMPARABLE_GROUP",
                          "expected_decision": "REJECT_COMPARISON", "reason": "Synthetic comparison request mixes non-equivalent roles."})
    proposals = pd.DataFrame(proposals, columns=["adjustment_id","employee_id","proposed_salary","currency","status","created_date","approved_by","reason"])
    comparison_requests = pd.DataFrame(columns=["comparison_id","employee_id_a","employee_id_b","rationale"])
    if n_employees >= 2:
        # Pick a guaranteed non-comparable pair (different role, level or location).
        pair_a, pair_b = 0, 1
        for candidate in range(1, n_employees):
            a, b = employees.iloc[pair_a], employees.iloc[candidate]
            if (a.role_id, a.level_id, a.location_id) != (b.role_id, b.level_id, b.location_id):
                pair_b = candidate
                break
        comparison_requests = pd.DataFrame([{
            "comparison_id": "CMP-2026-000001",
            "employee_id_a": employees.iloc[pair_a].employee_id,
            "employee_id_b": employees.iloc[pair_b].employee_id,
            "rationale": ""
        }])
    tables = {"roles": roles, "levels": levels, "locations": locations, "compensation_bands": bands,
              "employees": employees, "salary_records": salaries, "performance_evidence": performance,
              "tenure": tenures, "promotions": promotions, "adjustment_proposals": proposals,
              "comparison_requests": comparison_requests}
    for name, df in tables.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)
    with open(truth_dir / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump({"seed": seed, "labels": truth}, f, indent=2)

    manifest = {"seed": seed, "employee_count": len(employees), "salary_record_count": len(salaries),
                "role_count": len(roles), "level_count": len(levels), "location_count": len(locations),
                "band_count": len(bands), "files": {}}
    for name in tables:
        p = output_dir / f"{name}.csv"
        manifest["files"][p.name] = {"rows": len(tables[name]), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return tables, truth

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--employees", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=Path, default=DATA_DIR)
    parser.add_argument("--truth", type=Path, default=GROUND_TRUTH_DIR)
    args = parser.parse_args()
    tables, truth = generate_dataset(args.employees, args.seed, args.output, args.truth)
    print(f"Generated {len(tables['employees'])} employees, {len(tables['salary_records'])} salary records, {len(truth)} labelled cases.")
if __name__ == "__main__":
    main()
