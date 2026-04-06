# Rate Tracker 📊

A production-style data pipeline and API system that ingests, stores, and visualizes financial rate data.

---

## 🚀 Features

* Bulk data ingestion from Parquet (~1M rows)
* Idempotent data processing (no duplicates)
* REST APIs using Django REST Framework
* Token-based authentication for secure endpoints
* React dashboard (optional frontend)
* Auto-refreshing UI (every 60 seconds)

---

## 🛠 Tech Stack

* Backend: Django, Django REST Framework
* Database: SQLite (for local setup)
* Data Processing: Pandas, PyArrow
* Frontend: React
* API Testing: Postman

---

## 📦 Prerequisites

* Python 3.10+
* pip
* Node.js (for frontend)

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone <your-private-repo-url>
cd rate-tracker
```

---

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # mac/linux
venv\Scripts\activate     # windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run migrations

```bash
python manage.py migrate
```

---

### 5. Run data ingestion

```bash
python manage.py seed_data
```

---

### 6. Start server

```bash
python manage.py runserver
```

---

## 📡 API Endpoints

### 🔹 GET /rates/latest

Returns latest rate per provider

Optional:

```
/rates/latest?type=home_loan
```

---

### 🔹 GET /rates/history

Returns historical rates

Example:

```
/rates/history?provider=SBI&type=home_loan
```

---

### 🔹 POST /rates/ingest (Protected)

Headers:

```
Authorization: Token <your_token>
```

Body:

```json
{
  "provider_name": "TEST_BANK",
  "rate_type": "home_loan",
  "rate_value": 8.25,
  "effective_date": "2024-01-01"
}
```

---

## 🔐 Authentication

Token-based authentication is used for POST endpoint.

Generate token:

```bash
python manage.py drf_create_token <username>
```

---

## 🧪 Testing

Use Postman or curl to test APIs.

Example:

```bash
GET http://127.0.0.1:8000/rates/latest
```

---

## 📊 Frontend

If frontend is included:

```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Architecture Overview

```text
Parquet File → Ingestion Script → Database → REST APIs → React UI
```

---

## 🧠 Design & Thought Process

The system is designed as a simple but production-oriented data pipeline with clear separation of concerns.

### 🔹 Ingestion Layer

* Reads large Parquet datasets (~1M rows)
* Processes data in batches (5000 rows) to avoid memory issues
* Applies cleaning (null removal, trimming, type validation)
* Ensures idempotency using database-level unique constraints and conflict-safe inserts

### 🔹 Database Layer

* Stores structured rate data with indexing for efficient queries
* Supports:

  * Latest rate per provider
  * Time-series queries
  * Date-range filtering

### 🔹 API Layer

* Built using Django REST Framework
* Handles filtering, pagination, and structured responses
* Keeps views lightweight and logic clean
* Secures ingestion endpoint using token authentication

### 🔹 Frontend Layer

* React-based UI consuming real APIs
* Displays latest rates and historical trends
* Implements auto-refresh every 60 seconds
* Includes loading and error states

### 🔹 System Design Approach

* Focused on data integrity (idempotency)
* Designed for scalability (batch processing)
* Prioritized simplicity and maintainability

---

## 🧩 Technology Choices & Rationale

### 🔹 Django + DRF

* Rapid API development with strong ecosystem
* Built-in ORM simplifies database interaction

### 🔹 SQLite

* Lightweight and easy local setup
* Replaceable with PostgreSQL in production

### 🔹 Pandas + PyArrow

* Efficient handling of large Parquet datasets
* Simplifies data transformation

### 🔹 React

* Flexible and component-based UI development
* Easy API integration with hooks

### 🔹 Token Authentication

* Simple and effective security for ingestion endpoint

### 🔹 Batch Processing

* Prevents memory overload
* Improves performance for large inserts

---

## ⚠️ Notes

* Data ingestion uses batch processing (5000 rows)
* Duplicate records are avoided using unique constraints
* Designed for scalability and large datasets

---
