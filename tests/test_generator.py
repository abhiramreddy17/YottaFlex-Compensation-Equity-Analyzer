import pandas as pd
from app.data_generator import generate_dataset
from app.validation import validate_tables

def test_small_dataset_valid_and_deterministic(tmp_path):
    d1, truth1 = generate_dataset(50, 20261022, tmp_path/"a", tmp_path/"ta")
    d2, truth2 = generate_dataset(50, 20261022, tmp_path/"b", tmp_path/"tb")
    assert len(d1["employees"]) == 50
    assert len(d1["compensation_bands"]) == 240
    assert validate_tables(d1)["valid"]
    assert truth1 == truth2
    pd.testing.assert_frame_equal(d1["employees"], d2["employees"])
