"""Week 3 starter: rerunnable ingestion to a raw area.
Students implement file ingestion + paginated REST API ingestion + watermark + duplicate prevention.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; RAW=ROOT/'raw'; STATE=ROOT/'state'
API_URL='http://127.0.0.1:8000/api/events'

def utc_now(): return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def load_watermark():
    p=STATE/'api_watermark.json'
    if not p.exists(): return None
    return json.loads(p.read_text())['updated_at']

def save_watermark(value):
    STATE.mkdir(exist_ok=True)
    tmp_path = STATE/'api_watermark.json.tmp'
    tmp_path.write_text(json.dumps({'updated_at':value},indent=2))
    tmp_path.replace(STATE/'api_watermark.json')

def ingest_files():
    raw_files = RAW/'files'
    raw_files.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_files/'manifest.json'

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = []

    existing_hashes = {entry['sha256'] for entry in manifest}

    source_files = ['customers.csv', 'orders.json', 'products.parquet']
    records_written = 0
    duplicates_skipped = 0

    for filename in source_files:
        source_path = DATA/filename
        file_hash = sha256_file(source_path)

        if file_hash in existing_hashes:
            duplicates_skipped += 1
            print(f"Skipped {filename}: content hash already ingested")
            continue

        dest_path = raw_files/filename
        shutil.copy2(source_path, dest_path)

        manifest.append({
            'source_file': filename,
            'ingested_at': utc_now(),
            'bytes': source_path.stat().st_size,
            'sha256': file_hash
        })
        existing_hashes.add(file_hash)
        records_written += 1
        print(f"Copied {filename} to raw/files/, sha256={file_hash[:12]}...")

    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"ingest_files: {records_written} copied, {duplicates_skipped} skipped as already ingested")

    return {
        'records_read': len(source_files),
        'records_written': records_written,
        'duplicates_removed': duplicates_skipped
    }

def fetch_api_page(page, per_page=20, updated_after=None):
    params={'page':page,'per_page':per_page}
    if updated_after: params['updated_after']=updated_after
    r=requests.get(API_URL,params=params,timeout=30); r.raise_for_status(); return r.json()

def ingest_api():
    watermark_before = load_watermark()
    fetched = []
    page = 1
    while True:
        response = fetch_api_page(page, per_page=20, updated_after=watermark_before)
        for item in response['items']:
            item['_ingested_at'] = utc_now()
            item['_source'] = 'api'
            fetched.append(item)
        if response['has_more']:
            page += 1
        else:
            break

    raw_api = RAW/'api'
    raw_api.mkdir(parents=True, exist_ok=True)
    events_path = raw_api/'events.jsonl'

    existing = {}
    if events_path.exists():
        with events_path.open() as f:
            for line in f:
                record = json.loads(line)
                existing[record['event_id']] = record

    combined_count_before = len(existing) + len(fetched)

    merged = dict(existing)
    for record in fetched:
        event_id = record['event_id']
        if event_id not in merged or record['updated_at'] > merged[event_id]['updated_at']:
            merged[event_id] = record

    duplicates_removed = combined_count_before - len(merged)
    records_written = 0
    watermark_after = watermark_before

    if fetched:
        tmp_path = events_path.with_suffix('.jsonl.tmp')
        with tmp_path.open('w') as f:
            for record in merged.values():
                f.write(json.dumps(record) + '\n')
        tmp_path.replace(events_path)

        watermark_after = max(record['updated_at'] for record in merged.values())
        save_watermark(watermark_after)
        records_written = len(merged) - len(existing)

    print(f"ingest_api: fetched={len(fetched)}, duplicates_removed={duplicates_removed}, records_written={records_written}, watermark_before={watermark_before}, watermark_after={watermark_after}")

    return {
        'records_read': len(fetched),
        'records_written': records_written,
        'duplicates_removed': duplicates_removed,
        'watermark_before': watermark_before,
        'watermark_after': watermark_after
    }

if __name__=='__main__':
    RAW.mkdir(exist_ok=True); STATE.mkdir(exist_ok=True)
    ingest_files()
    ingest_api()