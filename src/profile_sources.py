"""Week 2 starter: profile CSV, JSON, Parquet, API payload, and PostgreSQL table.
Complete the TODOs. Do not hard-code expected counts.
"""
from pathlib import Path
import json, csv
import pandas as pd
DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def profile_csv(path):
    """Profile a CSV source: size, shape, dtypes, missing values, duplicates, key uniqueness."""
    file_size_bytes = path.stat().st_size
    df = pd.read_csv(path)

    print(f"=== Profiling: {path.name} ===")
    print(f"File size: {file_size_bytes:,} bytes ({file_size_bytes / 1024:.1f} KB)")
    print(f"Row count: {len(df)}")
    print(f"Column count: {len(df.columns)}")

    print("\n--- Columns: pandas dtype + sample values ---")
    for col in df.columns:
        sample = df[col].dropna().iloc[:3].tolist()
        print(f"  {col}: dtype={df[col].dtype}, sample={sample}")

    print("\n--- Missing values by column ---")
    missing_counts = df.isnull().sum()
    for col, count in missing_counts.items():
        pct = count / len(df)
        print(f"  {col}: {count} missing ({pct:.1%})")

    print("\n--- Duplicate rows (exact, all columns) ---")
    exact_duplicates = df[df.duplicated(keep=False)]
    print(f"  Exact duplicate rows: {len(exact_duplicates)}")

    print("\n--- Key uniqueness: customer_id ---")
    duplicate_ids = df[df['customer_id'].duplicated(keep=False)]
    print(f"  Unique customer_id values: {df['customer_id'].nunique()} of {len(df)} rows")
    print(f"  Rows involved in duplicate customer_id: {len(duplicate_ids)}")

    return df

def profile_json(path):
    # TODO: record count, keys, nested fields, date/time fields, numeric fields, nulls
    pass

def profile_parquet(path):
    # TODO: use pandas.read_parquet; report rows/columns/dtypes/nulls and file size
    # Requires pyarrow from requirements.txt
    pass

if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')