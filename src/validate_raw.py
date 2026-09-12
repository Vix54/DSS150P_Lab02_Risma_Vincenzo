"""Starter validation checks for raw outputs."""
from pathlib import Path
from datetime import datetime
import json

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'raw'
STATE=ROOT/'state'

def check(description, condition):
    status = 'PASS' if condition else 'FAIL'
    print(f"[{status}] {description}")
    return condition

def main():
    results = []

    expected_files = [
        RAW/'files'/'customers.csv',
        RAW/'files'/'orders.json',
        RAW/'files'/'products.parquet',
        RAW/'files'/'manifest.json',
        RAW/'api'/'events.jsonl',
        STATE/'api_watermark.json',
    ]
    for path in expected_files:
        results.append(check(f"Expected raw output exists: {path.relative_to(ROOT)}", path.exists()))

    events_path = RAW/'api'/'events.jsonl'
    records = []
    if events_path.exists():
        with events_path.open() as f:
            for line in f:
                records.append(json.loads(line))

    event_ids = [r['event_id'] for r in records]
    results.append(check("All event_id values in raw/api/events.jsonl are unique", len(event_ids) == len(set(event_ids))))

    required_fields = ['event_id', 'customer_id', 'event_type', 'amount', 'updated_at', '_ingested_at', '_source']
    all_fields_present = all(all(field in r for field in required_fields) for r in records)
    results.append(check("All API records contain required fields, including _ingested_at and _source", all_fields_present))

    all_timestamps_parseable = True
    for r in records:
        try:
            datetime.fromisoformat(r['updated_at'])
        except (ValueError, KeyError):
            all_timestamps_parseable = False
            break
    results.append(check("All updated_at values parse as valid ISO timestamps", all_timestamps_parseable))

    watermark_path = STATE/'api_watermark.json'
    if watermark_path.exists() and records:
        saved_watermark = json.loads(watermark_path.read_text())['updated_at']
        actual_max = max(r['updated_at'] for r in records)
        results.append(check(f"Saved watermark ({saved_watermark}) equals max(updated_at) in raw file ({actual_max})", saved_watermark == actual_max))
    else:
        results.append(check("Watermark equals max(updated_at) in raw file", False))

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")

    if passed != total:
        raise SystemExit(1)

if __name__=='__main__': main()