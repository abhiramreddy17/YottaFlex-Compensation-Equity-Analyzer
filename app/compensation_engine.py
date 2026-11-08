"""Compensation normalization and band calculations."""
import pandas as pd

def normalize_salary(amount, currency, fte, fx_rates, employee_fte=None):
    if currency not in fx_rates:
        return None
    if fte is None or float(fte) <= 0:
        return None
    # Annualized part-time salary is divided by recorded FTE to obtain FTE equivalent.
    normalized = float(amount) * float(fx_rates[currency]) / float(fte)
    return normalized

def compa_ratio(normalized_salary, midpoint_inr):
    if normalized_salary is None or midpoint_inr is None or float(midpoint_inr) <= 0:
        return None
    return float(normalized_salary) / float(midpoint_inr)

def within_band_position(normalized_salary, minimum_inr, maximum_inr):
    if normalized_salary is None or maximum_inr <= minimum_inr:
        return None
    return (float(normalized_salary) - float(minimum_inr)) / (float(maximum_inr) - float(minimum_inr))

def analyze_records(employees, salary_records, bands, locations):
    """Return latest salary row per employee enriched with derived metrics."""
    if employees.empty or salary_records.empty:
        return pd.DataFrame()
    latest = salary_records.sort_values("effective_date").groupby("employee_id", as_index=False).tail(1).copy()
    data = latest.merge(employees, on="employee_id", suffixes=("_salary", "_employee"), validate="many_to_one")
    data = data.merge(bands, on="band_id", how="left", suffixes=("", "_band"), validate="many_to_one")
    data = data.merge(locations[["location_id", "city"]], on="location_id", how="left", validate="many_to_one")
    fx = {"INR": 1.0, "USD": 83.0, "GBP": 105.0}
    # Salary currency comes from SalaryRecord; band currency comes from CompensationBand.
    # After the employee merge, the salary field is named currency_salary. The band
    # merge contributes its own unsuffixed currency column.
    salary_currency_col = "currency_salary" if "currency_salary" in data.columns else "currency"
    band_currency_col = "currency_band" if "currency_band" in data.columns else "currency"
    data["normalized_salary_inr"] = data.apply(
        lambda r: normalize_salary(r["base_salary"], r[salary_currency_col], r["fte_at_record"], fx), axis=1)
    # Bands are stored in their native currency. Convert to INR for consistent comparison.
    data["band_min_inr"] = data.apply(lambda r: r["min_salary"] * fx.get(r[band_currency_col], float("nan")), axis=1)
    data["band_mid_inr"] = data.apply(lambda r: r["mid_salary"] * fx.get(r[band_currency_col], float("nan")), axis=1)
    data["band_max_inr"] = data.apply(lambda r: r["max_salary"] * fx.get(r[band_currency_col], float("nan")), axis=1)
    data["compa_ratio"] = data.apply(lambda r: compa_ratio(r["normalized_salary_inr"], r["band_mid_inr"]), axis=1)
    data["within_band_position"] = data.apply(
        lambda r: within_band_position(r["normalized_salary_inr"], r["band_min_inr"], r["band_max_inr"]), axis=1)
    return data

def comparable_group_key(row):
    return (row.get("role_id"), row.get("level_id"), row.get("location_id"))
