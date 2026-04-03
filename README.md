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

## ⚠️ Notes

* Data ingestion uses batch processing (5000 rows)
* Duplicate records are avoided using unique constraints
* Designed for scalability and large datasets

---

---
