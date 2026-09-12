# Source Profiling Report

## 1. Source Inventory

| Source | Type | Rows/Records | Key | Update Pattern | Quality Findings |
|---|---|---:|---|---|---|
| customers.csv | CSV | 250 | customer_id (3 duplicate values, 6 rows) | Full load, static snapshot | 1 genuine ID clash (C0090) between two different people; 4 exact duplicate rows; email missing in 1.2% of rows; city missing in 0.8% |
| orders.json | JSON | 250 | order_id | Full load, static snapshot | No missing keys or null values; number formats are consistent across the whole dataset |
| products.parquet | Parquet | 200 | product_id | Full load, static snapshot | No missing values; file size is larger than the CSV version at 200 rows; stock_quantity loads accurately as int32 |
| api_events (REST API) | REST API | 122 | event_id (2 duplicate values) | Incremental via updated_after and persisted watermark | 2 duplicate event_id values with different amounts and updated_at times; requires deduplication by latest timestamp |
| support_tickets | PostgreSQL | 250 | ticket_id (declared primary key) | Read-only inspection for this project | assigned_agent missing for 4 tickets; resolved_at missing for open tickets; no strict database link (foreign key) to the customers data |

## 2. Schema Findings

How we handle data types depends entirely on the source. CSV and JSON files don't store built-in rules, so everything comes in as plain text or basic JSON formats. This means we have to manually set the logical types later in the pipeline—like making sure `signup_date` and `order_timestamp` are read as real dates and not just text strings. Parquet is different because it saves the schema directly inside the file. That's why `stock_quantity` loads efficiently as a smaller `int32`, while the CSV version defaults to a larger `int64` because it lacks those saved rules. PostgreSQL gives us the strongest structure, with strict column types, rules for blank values, and a set primary key. However, it's worth noting that there is no database rule (foreign key) linking `customer_id` in the tickets to the `customers` dataset. Right now, matching them up relies on an assumption rather than an enforced rule.

## 3. Data Quality Findings

1. `customers.csv` has three duplicate `customer_id` values. Two of these are just exact copies (C0036, C0145), but one (C0090) is a real clash where two completely different people share the same ID.
2. `customers.csv` is missing `email` data in 1.2% of its rows and `city` data in 0.8%.
3. `orders.json` is perfectly clean. There are zero missing keys, zero null values, and the number formats are consistent across all 250 records.
4. `products.parquet` actually takes up more space (14,652 bytes) than its CSV version (11,560 bytes) at 200 rows. This shows that for very small datasets, Parquet's built-in schema takes up more space than its compression saves.
5. The `api_events` source has two duplicate `event_id` records (E0020, E0055). Each duplicate has a different `amount` and a later `updated_at` time, which matches the intentional duplicates planted for this assignment.
6. Just pulling page 1 of the REST API (with the default 20 items per page) only gets 20 of the 122 records, leaving out about 84% of the dataset.
7. The `support_tickets` database doesn't have a strict rule linking its `customer_id` to the actual `customers` data, even though they share the same naming convention.

## 4. Recommended Acquisition Method

* **`customers.csv`, `orders.json`, `products.parquet`:** Just copy the files into `raw/files/` and use a SHA-256 hash check to make sure we don't copy the same file twice. We need to do a full load every time since these files don't have an `updated_at` timestamp.
* **REST API (`api_events`):** Use paginated GET requests to pull everything until there are no more pages left (`has_more == false`). Save the latest `updated_at` time so we can do incremental pulls on future runs. We also need to add a code step to remove duplicates by `event_id`, keeping only the row with the most recent `updated_at`.
* **PostgreSQL (`support_tickets`):** For this project, stick to read-only queries with strict limits so we don't slow down the live database. If we want to do incremental pulls later, we'd need to check both the `opened_at` and `resolved_at` timestamps, or use Change Data Capture (CDC) to track every single update.

## 5. Risks and Assumptions

* The API's incremental pull assumes the `updated_at` timestamp is precise enough to sort everything in order. But it only tracks down to the second, meaning two different events could technically share the exact same timestamp.
* Our cleanup rule assumes that keeping the record with the newest `updated_at` is the right business logic for `api_events`. This was guessed based on the project's setup; it wasn't confirmed by the data owners.
* We don't have a fix yet for the ID clash (C0090) in `customers.csv`. If someone downstream just removes duplicates by `customer_id`, they will silently delete a real customer's data without any warning.
* We are treating all file sources as static snapshots. Our setup assumes that the source files won't be edited or changed after we ingest them.
* The file size comparison between Parquet and CSV only applies to this specific 200-row dataset. We expect Parquet to be much better at saving space with real, large-scale data, but we haven't tested that here.
* Since there's no strict link between `customer_id` in `support_tickets` and the `customers` source, joining them together later assumes the data matches up correctly without any built-in safety net.