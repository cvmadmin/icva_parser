#!/usr/bin/env python3
"""
load_vea_2025.py

Quick utility to load the VEA 2025 CSV results into a MariaDB table.

Usage:
    # Activate your virtualenv first, then:
    python load_vea_2025.py --csv vea_2025_results.csv

Environment variables are read from a .env file in the working directory. Example:

    DB_HOST=cvmdb.westernu.edu
    DB_USER=your_user
    DB_PASS=your_password
    DB_NAME=cvm_prod
    DB_TABLE=vea_2025   # optional; defaults to vea_2025 if omitted
"""
import os
from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text


def load_env() -> dict:
    """Load DB settings from .env and return as dict."""
    load_dotenv()
    cfg = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "database": os.getenv("DB_NAME"),
        "table": os.getenv("DB_TABLE"),
    }
    missing = [k for k, v in cfg.items() if v in (None, "",) and k != "table"]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")
    return cfg


def create_table(engine, table_name: str) -> None:
    """Create the vea_2025 table if it doesn't already exist."""
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        `icva_id`         VARCHAR(12)  PRIMARY KEY,
        `full_name`       VARCHAR(100),
        `test_date`       DATE,
        `vea_score`       INT,
        `vea_percentage`  INT,
        `vea_anatomy`     INT,
        `vea_physiology`  INT,
        `vea_pharmacology` INT,
        `vea_microbiology` INT,
        `vea_pathology`    INT
    ) CHARACTER SET utf8mb4;
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))


def main(csv_path: Path) -> None:
    cfg = load_env()

    # Build SQLAlchemy engine for MariaDB / MySQL
    engine_url = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}/{cfg['database']}"
    )
    engine = create_engine(engine_url, future=True)

    # Read the CSV
    df = pd.read_csv(csv_path)
    # Parse the test_date column into real DATE objects
    if "test_date" in df.columns:
        df["test_date"] = pd.to_datetime(df["test_date"], format="%d-%b-%Y").dt.date

    # Create table if needed
    create_table(engine, cfg["table"])

    # Insert data (append, skip existing primary keys)
    with engine.begin() as conn:
        df.to_sql(
            name=cfg["table"],
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            dtype=None,  # let pandas infer
        )

    print(f"✅ Loaded {len(df):,} rows into `{cfg['table']}`.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load VEA 2025 CSV results into a MariaDB table."
    )
    parser.add_argument(
        "--csv",
        default="vea_2025_results.csv",
        type=Path,
        help="Path to the CSV file (default: vea_2025_results.csv)",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"❌ CSV file '{args.csv}' not found.", file=sys.stderr)
        sys.exit(1)

    main(args.csv)