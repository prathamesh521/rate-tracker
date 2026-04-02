"""
tests.py
--------
Test suite for the rates API.

Run with:
    cd rateTracker
    python manage.py test apps.rates --verbosity=2

Covers:
  - GET  /rates/latest   (basic response, ?type= filter, caching)
  - GET  /rates/history  (pagination, filters)
  - POST /rates/ingest   (valid payload, invalid payload, idempotency, auth)
"""

import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.rates.models import Rate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rate(**kwargs) -> Rate:
    """Create and return a Rate with sensible defaults."""
    defaults = {
        "provider_name": "TestBank",
        "rate_type": "home_loan",
        "rate_value": 5.0,
        "effective_date": datetime.date(2024, 1, 1),
    }
    defaults.update(kwargs)
    return Rate.objects.create(**defaults)


class AuthenticatedAPITestCase(TestCase):
    """Base class that sets up a token-authenticated client."""

    def setUp(self):
        super().setUp()
        # LocMemCache is shared within the test process; clear it so cached
        # responses from one test method never bleed into the next.
        cache.clear()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.token = Token.objects.create(user=self.user)
        self.auth_client = APIClient()
        self.auth_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.anon_client = APIClient()


# ---------------------------------------------------------------------------
# GET /rates/latest
# ---------------------------------------------------------------------------

class LatestRatesViewTest(AuthenticatedAPITestCase):
    """Tests for GET /rates/latest."""

    def test_returns_200_with_no_data(self):
        response = self.client.get("/rates/latest")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_returns_latest_rate_per_provider_type(self):
        """Only the most-recent row per (provider, type) is returned."""
        older = _make_rate(
            provider_name="ANZ",
            rate_type="home_loan",
            rate_value=4.5,
            effective_date=datetime.date(2024, 1, 1),
        )
        newer = _make_rate(
            provider_name="ANZ",
            rate_type="home_loan",
            rate_value=5.25,
            effective_date=datetime.date(2024, 6, 1),
        )

        response = self.client.get("/rates/latest")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["rate_value"], newer.rate_value)
        self.assertEqual(response.data[0]["effective_date"], str(newer.effective_date))
        # Older row must NOT appear
        ids = [r["id"] for r in response.data]
        self.assertNotIn(older.id, ids)

    def test_returns_one_row_per_provider_type_combination(self):
        """Multiple (provider, type) pairs each return their own latest row."""
        _make_rate(provider_name="ANZ", rate_type="home_loan", rate_value=5.0,
                   effective_date=datetime.date(2024, 1, 1))
        _make_rate(provider_name="ANZ", rate_type="savings", rate_value=2.0,
                   effective_date=datetime.date(2024, 1, 1))
        _make_rate(provider_name="CBA", rate_type="home_loan", rate_value=4.8,
                   effective_date=datetime.date(2024, 1, 1))

        response = self.client.get("/rates/latest")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_type_filter_returns_only_matching_rates(self):
        _make_rate(provider_name="ANZ", rate_type="home_loan", rate_value=5.0,
                   effective_date=datetime.date(2024, 1, 1))
        _make_rate(provider_name="CBA", rate_type="savings", rate_value=2.0,
                   effective_date=datetime.date(2024, 1, 1))

        response = self.client.get("/rates/latest?type=home_loan")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["rate_type"], "home_loan")

    def test_type_filter_is_case_insensitive(self):
        _make_rate(provider_name="ANZ", rate_type="home_loan",
                   effective_date=datetime.date(2024, 1, 1))

        response = self.client.get("/rates/latest?type=HOME_LOAN")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_response_is_cached(self):
        """A second identical request should return cached data (same count)."""
        _make_rate(effective_date=datetime.date(2024, 1, 1))

        r1 = self.client.get("/rates/latest")
        r2 = self.client.get("/rates/latest")

        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r1.data), len(r2.data))


# ---------------------------------------------------------------------------
# GET /rates/history
# ---------------------------------------------------------------------------

class RateHistoryViewTest(AuthenticatedAPITestCase):
    """Tests for GET /rates/history."""

    def setUp(self):
        super().setUp()
        _make_rate(provider_name="ANZ", rate_type="home_loan", rate_value=5.0,
                   effective_date=datetime.date(2024, 1, 1))
        _make_rate(provider_name="ANZ", rate_type="home_loan", rate_value=5.5,
                   effective_date=datetime.date(2024, 6, 1))
        _make_rate(provider_name="CBA", rate_type="savings", rate_value=2.0,
                   effective_date=datetime.date(2024, 3, 1))

    def test_returns_all_records_paginated(self):
        response = self.client.get("/rates/history")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 3)

    def test_ordered_by_effective_date_desc(self):
        response = self.client.get("/rates/history")
        dates = [r["effective_date"] for r in response.data["results"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_provider_filter(self):
        response = self.client.get("/rates/history?provider=ANZ")
        self.assertEqual(response.data["count"], 2)
        for r in response.data["results"]:
            self.assertIn("ANZ", r["provider_name"])

    def test_type_filter(self):
        response = self.client.get("/rates/history?type=savings")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["rate_type"], "savings")

    def test_from_date_filter(self):
        response = self.client.get("/rates/history?from=2024-04-01")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["effective_date"], "2024-06-01")

    def test_to_date_filter(self):
        response = self.client.get("/rates/history?to=2024-02-01")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["effective_date"], "2024-01-01")

    def test_combined_filters(self):
        response = self.client.get(
            "/rates/history?provider=ANZ&type=home_loan&from=2024-01-01&to=2024-03-01"
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["effective_date"], "2024-01-01")

    def test_pagination_page_size(self):
        response = self.client.get("/rates/history?page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])


# ---------------------------------------------------------------------------
# POST /rates/ingest
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "provider_name": "ANZ",
    "rate_type": "home_loan",
    "rate_value": 5.25,
    "effective_date": "2024-03-01",
}


class RateIngestViewTest(AuthenticatedAPITestCase):
    """Tests for POST /rates/ingest."""

    # --- Authentication ---

    def test_unauthenticated_request_returns_401(self):
        response = self.anon_client.post("/rates/ingest", VALID_PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Valid payload ---

    def test_valid_payload_creates_record(self):
        response = self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rate.objects.count(), 1)

    def test_created_response_contains_expected_fields(self):
        response = self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")
        data = response.data
        self.assertEqual(data["provider_name"], "ANZ")
        self.assertEqual(data["rate_type"], "home_loan")
        self.assertAlmostEqual(data["rate_value"], 5.25, places=4)
        self.assertEqual(data["effective_date"], "2024-03-01")
        self.assertIn("id", data)
        self.assertIn("ingestion_timestamp", data)

    # --- Idempotency ---

    def test_duplicate_insert_returns_200_not_201(self):
        """Sending the same record twice should update (200) not re-create (201)."""
        r1 = self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")
        r2 = self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(Rate.objects.count(), 1)

    def test_duplicate_insert_updates_rate_value(self):
        """Updating the rate_value for an existing (provider, type, date) triple."""
        self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")

        updated_payload = {**VALID_PAYLOAD, "rate_value": 6.00}
        self.auth_client.post("/rates/ingest", updated_payload, format="json")

        rate = Rate.objects.get()
        self.assertAlmostEqual(rate.rate_value, 6.00, places=4)

    # --- Invalid payloads ---

    def test_missing_required_field_returns_400(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "rate_value"}
        response = self.auth_client.post("/rates/ingest", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_blank_provider_name_returns_400(self):
        response = self.auth_client.post(
            "/rates/ingest", {**VALID_PAYLOAD, "provider_name": "  "}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_rate_value_returns_400(self):
        response = self.auth_client.post(
            "/rates/ingest", {**VALID_PAYLOAD, "rate_value": -1.0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_format_returns_400(self):
        response = self.auth_client.post(
            "/rates/ingest", {**VALID_PAYLOAD, "effective_date": "not-a-date"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_body_returns_400(self):
        response = self.auth_client.post("/rates/ingest", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    # --- Cache invalidation ---

    def test_ingest_invalidates_latest_cache(self):
        """After ingest, /rates/latest should reflect the new record."""
        # Warm the cache with an empty response
        r_before = self.client.get("/rates/latest")
        self.assertEqual(r_before.data, [])

        # Ingest a new record
        self.auth_client.post("/rates/ingest", VALID_PAYLOAD, format="json")

        # The cached empty response should be gone
        r_after = self.client.get("/rates/latest")
        self.assertEqual(len(r_after.data), 1)
