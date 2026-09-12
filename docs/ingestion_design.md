# Ingestion Design Task 2.4

| Source | Method | Raw destination | Duplicate key | Incremental state |
|---|---|---|---|---|
| CSV / JSON / Parquet | File copy + manifest | raw/files/ | File SHA-256 | N/A |
| REST API | Paginated GET | raw/api/events.jsonl | event_id | max(updated_at) |
| PostgreSQL | Inspection only in this project | N/A | ticket_id | See discussion below |

## PostgreSQL incremental strategy discussion

This project only inspects `support_tickets` via bounded read-only queries; no ingestion pipeline is implemented against it. If this source were extended to a full incremental design, two realistic strategies exist.

Timestamp-based watermark: support_tickets has no single "last updated" column. opened_at only reflects ticket creation, and resolved_at stays null until a ticket closes. A composite check such as opened_at > watermark OR resolved_at > watermark could catch new and newly-resolved tickets, but would miss any in-place update to a field like priority or assigned_agent, since neither timestamp advances when only those change.

Change Data Capture: a WAL-based approach captures every INSERT/UPDATE/DELETE regardless of which column changed, without depending on the table having a reliable timestamp at all. Heavier to operate, but has no blind spot for silent field-level updates.

Given this exercise's constraint of read-only, non-destructive source access, no ingestion was implemented against this source consistent with the project's rule against placing unnecessary load on a source system.

## Watermark semantics (Task 2.5)

**If the watermark is saved before the raw file is successfully written:** a crash or failed write after the watermark advances means the next run believes those records were already captured, since it only requests updated_after the new watermark. 

**If the source allows multiple records with the exact same timestamp:** a batch boundary could split a group of same-timestamp records across two page fetches. Once the watermark advances past that timestamp, any records sharing it that weren't captured in the first batch are permanently skipped on the next run the watermark has no way to express "some but not all records at this exact timestamp were seen."

**Limitation:** this watermark assumes updated_at is fine-grained enough to uniquely order records, but the API only carries second-level precision with no guarantee against collisions.

**Production-grade mitigation:** use a compound cursor, sorted and compared as a tuple instead of a bare timestamp, this lets the watermark resume after a specific record rather than after a point in time. Notably, the API already sorts by exactly this tuple; the current watermark design just doesn't persist the full cursor, only half of it.