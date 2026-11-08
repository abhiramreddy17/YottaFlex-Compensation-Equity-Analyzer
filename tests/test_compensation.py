from app.compensation_engine import normalize_salary, compa_ratio, within_band_position

def test_normalize_salary_fte():
    assert normalize_salary(250000, "INR", 0.5, {"INR": 1.0}) == 500000

def test_compa_ratio():
    assert compa_ratio(500000, 500000) == 1.0

def test_within_band_position():
    assert within_band_position(500000, 400000, 600000) == 0.5

def test_missing_currency_returns_none():
    assert normalize_salary(100, "XYZ", 1.0, {"INR": 1.0}) is None
