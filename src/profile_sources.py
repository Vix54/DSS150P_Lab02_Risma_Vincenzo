"""Week 2 starter: profile CSV, JSON, Parquet, API payload, and PostgreSQL table.
Complete the TODOs. Do not hard-code expected counts.
"""
from pathlib import Path
import json, csv
import pandas as pd
DATA_DIR=Path(__file__).resolve().parents[1]/'data'

def profile_csv(path):
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

    print("\n--- Duplicate customer_id rows (detail) ---")
    dup_detail = df[df['customer_id'].duplicated(keep=False)].sort_values('customer_id')
    print(dup_detail.to_string(index=False))

    print(f"\ncustomer_segment unique values: {df['customer_segment'].unique().tolist()}")

    return df

def profile_json(path):
    with open(path) as f:
        data = json.load(f)

    print(f"=== Profiling: {path.name} ===")
    print(f"Root structure: {type(data).__name__}")
    print(f"Record count: {len(data)}")

    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    print(f"\nTop-level keys observed across all records: {sorted(all_keys)}")

    print("\n--- Per-field presence, nulls, and inferred type ---")
    for key in sorted(all_keys):
        present_count = sum(1 for r in data if key in r)
        missing_key_count = len(data) - present_count
        null_count = sum(1 for r in data if r.get(key) is None)
        sample_values = [r[key] for r in data if key in r and r[key] is not None][:3]
        value_types = {type(v).__name__ for v in sample_values}
        print(f"  {key}: present in {present_count}/{len(data)} "
              f"(missing key: {missing_key_count}, null value: {null_count}), "
              f"types seen={value_types}, sample={sample_values}")

    print("\n--- Nested field ---")
    nested_keys = [k for k in all_keys if any(isinstance(r.get(k), dict) for r in data)]
    print(f"  Nested (object-valued) fields: {nested_keys}")
    for nk in nested_keys:
        sub_keys = set()
        for r in data:
            if isinstance(r.get(nk), dict):
                sub_keys.update(r[nk].keys())
        print(f"  {nk} sub-keys: {sorted(sub_keys)}")

    print("\n--- Full-dataset type consistency (numeric fields) ---")
    for key in ['item_count', 'shipping_fee', 'subtotal', 'total_amount']:
        types_all = {type(r[key]).__name__ for r in data if key in r and r[key] is not None}
        print(f"  {key}: types across all 250 records = {types_all}")

    return data

def profile_parquet(path):
    file_size_bytes = path.stat().st_size
    df = pd.read_parquet(path)

    print(f"=== Profiling: {path.name} ===")
    print(f"File size: {file_size_bytes:,} bytes ({file_size_bytes / 1024:.1f} KB)")
    print(f"Row count: {len(df)}")
    print(f"Column count: {len(df.columns)}")

    print("\n--- Columns: dtype + sample values ---")
    for col in df.columns:
        sample = df[col].dropna().iloc[:3].tolist()
        print(f"  {col}: dtype={df[col].dtype}, sample={sample}")

    print("\n--- Missing values by column ---")
    missing_counts = df.isnull().sum()
    for col, count in missing_counts.items():
        pct = count / len(df)
        print(f"  {col}: {count} missing ({pct:.1%})")

    compare_csv = path.parent / 'products_optional_compare.csv'
    compare_json = path.parent / 'products_optional_compare.json'

    print("\n--- Format comparison: file size ---")
    print(f"  parquet: {file_size_bytes:,} bytes")
    if compare_csv.exists():
        print(f"  csv:     {compare_csv.stat().st_size:,} bytes")
    if compare_json.exists():
        print(f"  json:    {compare_json.stat().st_size:,} bytes")

    print("\n--- Format comparison: type preservation ---")
    print(f"  parquet dtypes (native, embedded in file): {df.dtypes.to_dict()}")
    if compare_csv.exists():
        df_csv = pd.read_csv(compare_csv)
        print(f"  csv dtypes (inferred by pandas at read time, not stored in file): {df_csv.dtypes.to_dict()}")

    return df

if __name__=='__main__':
    profile_csv(DATA_DIR/'customers.csv')
    profile_json(DATA_DIR/'orders.json')
    profile_parquet(DATA_DIR/'products.parquet')