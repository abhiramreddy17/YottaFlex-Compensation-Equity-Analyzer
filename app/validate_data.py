import json
import pandas as pd
from app.config import DATA_DIR
from app.validation import validate_tables
names = ["roles","levels","locations","compensation_bands","employees","salary_records",
         "performance_evidence","tenure","promotions","adjustment_proposals"]
tables = {n: pd.read_csv(DATA_DIR / f"{n}.csv") for n in names}
result = validate_tables(tables)
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["valid"] else 1)
