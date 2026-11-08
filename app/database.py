"""Optional SQLite persistence using SQLAlchemy; default local DB is compensation.db."""
from pathlib import Path
from sqlalchemy import create_engine, text
from app.config import ROOT

DB_PATH = ROOT / "compensation.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

def load_csv_tables(data_dir):
    import pandas as pd
    from app.validation import validate_tables
    tables = {p.stem: pd.read_csv(p) for p in Path(data_dir).glob("*.csv")}
    result = validate_tables(tables)
    if not result["valid"]:
        raise ValueError("; ".join(result["errors"]))
    with engine.begin() as conn:
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
    return {k: len(v) for k, v in tables.items()}

def table_counts():
    with engine.connect() as conn:
        names = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
        return {name: conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one() for name in names}
