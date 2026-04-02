# DECISIONS.md

## 1. Assumptions

| Assumption | Rationale |
|---|---|
| One authoritative rate per `(provider_name, rate_type, effective_date)` | A provider publishes at most one rate of each type per calendar day. The unique constraint enforces this. |
| `rate_value` is always non-negative | Interest rates below zero are valid in some markets, but excluded here to match the seed data and keep validation simple. |
| Read endpoints are public; write endpoint requires a token | Rates are public information; ingestion is an internal/admin operation. |
| SQLite is acceptable for development | The schema and ORM queries are written to be portable, so migrating to PostgreSQL requires only a settings change. |
| The parquet column may be named `provider` or `provider_name` | The cleaning step handles both silently via a rename. |

---

## 2. Idempotency Strategy

Idempotency is enforced at two levels:

**Bulk ingestion (`seed_data` management command)**
- `bulk_create(ignore_conflicts=True)` is used with the existing `UniqueConstraint` on `(provider_name, rate_type, effective_date)`.
- Duplicate rows are silently skipped by the database; no error is raised.
- Re-running the command with the same parquet file is safe and produces no side effects.

**Single-record ingestion (`POST /rates/ingest`)**
- `update_or_create` looks up by `(provider_name, rate_type, effective_date)` and updates `rate_value` if the record already exists.
- Returns `201 Created` for a new record, `200 OK` for an update — the caller can distinguish the two cases without any additional query.

---

## 3. One Tradeoff Made

**LocMemCache instead of Redis for caching**

`GET /rates/latest` uses Django's built-in `LocMemCache` (in-process memory) with a 60-second TTL and a version-bump invalidation strategy.

*Why:* Eliminates an external infrastructure dependency, making the project runnable with a single `pip install` and `python manage.py runserver`.

*Cost:* The cache is per-process and lost on restart. In a multi-worker deployment (e.g., gunicorn with 4 workers) each worker maintains its own cache, so invalidation on ingest only clears the cache in the worker that handled the ingest request. Switching to a shared cache backend (Redis via `django-redis`) removes this limitation with no code changes — only a one-line settings update.

---

## 4. One Thing I'd Improve with More Time

**Switch to PostgreSQL and use `DISTINCT ON` for `get_latest_rates`**

The current implementation uses a `NOT EXISTS` anti-join correlated subquery, which is efficient with the composite index on `(provider_name, rate_type, effective_date)` but still touches every row to evaluate the EXISTS predicate.

PostgreSQL's `DISTINCT ON (provider_name, rate_type) ORDER BY provider_name, rate_type, effective_date DESC` collapses the result to one row per group in a single index scan — no correlated subquery, no self-join. This is the canonical solution for "greatest-n-per-group" and scales to tens of millions of rows with constant query plan complexity.

The migration path is a one-line database settings change (SQLite → PostgreSQL), and the `DISTINCT ON` variant can be expressed cleanly in Django ORM using a `RawQuerySet` or a custom manager until Django exposes it natively.
