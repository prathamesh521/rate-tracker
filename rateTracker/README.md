# Rate Tracker API

A Django REST Framework service that ingests, stores, and serves interest rate data from financial providers.

---

## Setup

### 1. Create and activate a virtual environment

```bash
cd rate-tracker
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
cd rateTracker
python manage.py migrate
```

### 4. Create a superuser (required for the ingest token)

```bash
python manage.py createsuperuser
```

### 5. Generate an API token

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='<your-username>')
token, _ = Token.objects.get_or_create(user=user)
print('Token:', token.key)
"
```

Keep this token — you'll need it for `POST /rates/ingest`.

---

## Run the Development Server

```bash
cd rateTracker
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`.

---

## Seed Data from Parquet

Load the included seed file (or any compatible parquet file):

```bash
# Default path: ../data/rates_seed.parquet
python manage.py seed_data

# Custom path
python manage.py seed_data --file /path/to/rates.parquet

# Custom batch size (default 5000)
python manage.py seed_data --batch-size 2000
```

The command is **idempotent** — re-running it with the same file skips existing records safely.

---

## API Endpoints

### `GET /rates/latest`

Returns the most recent rate for every `(provider, type)` combination.
Responses are cached for 60 seconds and invalidated automatically on ingest.

**Query parameters:**

| Parameter | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `type`    | string | Filter by rate type (case-insensitive) |

**Examples:**

```http
GET http://127.0.0.1:8000/rates/latest
GET http://127.0.0.1:8000/rates/latest?type=home_loan
```

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "provider_name": "ANZ",
    "rate_type": "home_loan",
    "rate_value": 5.25,
    "effective_date": "2024-06-01",
    "ingestion_timestamp": "2024-06-01T10:30:00Z"
  }
]
```

---

### `GET /rates/history`

Returns paginated rate history with optional filters, ordered by `effective_date` descending.

**Query parameters:**

| Parameter   | Type   | Description                                |
|-------------|--------|--------------------------------------------|
| `provider`  | string | Partial match on provider name             |
| `type`      | string | Exact match on rate type (case-insensitive)|
| `from`      | date   | Filter `effective_date >= YYYY-MM-DD`      |
| `to`        | date   | Filter `effective_date <= YYYY-MM-DD`      |
| `page`      | int    | Page number (default: 1)                   |
| `page_size` | int    | Results per page (default: 50, max: 500)   |

**Examples:**

```http
GET http://127.0.0.1:8000/rates/history
GET http://127.0.0.1:8000/rates/history?provider=ANZ&type=home_loan
GET http://127.0.0.1:8000/rates/history?from=2024-01-01&to=2024-06-30
GET http://127.0.0.1:8000/rates/history?page=2&page_size=100
```

**Response `200 OK`:**

```json
{
  "count": 1500,
  "next": "http://127.0.0.1:8000/rates/history?page=2",
  "previous": null,
  "results": [
    {
      "id": 42,
      "provider_name": "ANZ",
      "rate_type": "home_loan",
      "rate_value": 5.25,
      "effective_date": "2024-06-01",
      "ingestion_timestamp": "2024-06-01T10:30:00Z"
    }
  ]
}
```

---

### `POST /rates/ingest`

Inserts or updates a single rate record. Requires Token authentication.

**Headers:**

```
Authorization: Token <your-token>
Content-Type: application/json
```

**Request body:**

```json
{
  "provider_name": "ANZ",
  "rate_type": "home_loan",
  "rate_value": 5.25,
  "effective_date": "2024-03-01"
}
```

**Responses:**

| Status | Meaning                              |
|--------|--------------------------------------|
| `201`  | New record created                   |
| `200`  | Existing record updated (idempotent) |
| `400`  | Validation error (see `errors` key)  |
| `401`  | Missing or invalid token             |

**Validation rules:**

- `provider_name` — required, non-blank string, max 255 chars
- `rate_type` — required, non-blank string, max 100 chars
- `rate_value` — required, non-negative float
- `effective_date` — required, `YYYY-MM-DD` format

---

## Testing with Postman

### Step 1 — Import collection

Create requests manually or import using the base URL `http://127.0.0.1:8000`.

### Step 2 — GET /rates/latest

- Method: `GET`
- URL: `http://127.0.0.1:8000/rates/latest`
- No authentication needed

Add `?type=home_loan` to filter results.

### Step 3 — GET /rates/history

- Method: `GET`
- URL: `http://127.0.0.1:8000/rates/history`
- Add query params in the **Params** tab:
  - `provider` → `ANZ`
  - `from` → `2024-01-01`
  - `to` → `2024-12-31`

### Step 4 — POST /rates/ingest (with token)

1. Method: `POST`
2. URL: `http://127.0.0.1:8000/rates/ingest`
3. **Auth tab** → Type: `API Key`
   - Key: `Authorization`
   - Value: `Token <your-token>`
   - Add to: `Header`
4. **Body tab** → raw → JSON:
   ```json
   {
     "provider_name": "Westpac",
     "rate_type": "fixed_3yr",
     "rate_value": 6.10,
     "effective_date": "2024-09-01"
   }
   ```
5. Send — expect `201 Created`.
6. Send again with the same body — expect `200 OK` (idempotent).

---

## Running Tests

```bash
cd rateTracker
python manage.py test apps.rates --verbosity=2
```

The test suite covers:

- `GET /rates/latest` — empty state, latest-per-group logic, `?type=` filter, caching
- `GET /rates/history` — pagination, date range filters, provider/type filters, ordering
- `POST /rates/ingest` — valid payload (201), idempotent update (200), invalid payloads (400), unauthenticated (401), cache invalidation

---

## Project Structure

```
rateTracker/
├── rateTracker/          # Django project settings & routing
│   ├── settings.py
│   └── urls.py
├── apps/
│   └── rates/
│       ├── models.py         # Rate model
│       ├── serializers.py    # Request/response serializers
│       ├── views.py          # Thin API views
│       ├── urls.py           # URL routing
│       ├── tests.py          # Test suite
│       └── services/
│           ├── rate_service.py       # Read queries
│           └── ingestion_service.py  # Write / batch-insert logic
│       └── management/commands/
│           └── seed_data.py          # Parquet ingestion command
├── DECISIONS.md
└── README.md
```
