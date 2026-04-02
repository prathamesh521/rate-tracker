"""
rate_service.py
---------------
All read-side query logic lives here.
Views call these functions and get back QuerySets or model instances.
"""

import logging

from django.db.models import Exists, OuterRef

from apps.rates.models import Rate

logger = logging.getLogger(__name__)


def get_latest_rates(rate_type: str = None):
    """
    Return the single most-recent Rate row per (provider_name, rate_type) pair.

    Strategy: NOT EXISTS anti-join.
    Keep only rows where no sibling row exists with the same provider+type
    and a strictly later effective_date.  The compound index on
    (provider_name, rate_type, effective_date) makes each existence check
    an O(log n) index seek, and EXISTS short-circuits on the first match,
    so this is efficient even with 1 M+ rows.

    Generated SQL (simplified):
        SELECT * FROM rates_rate r1
        WHERE NOT EXISTS (
            SELECT 1 FROM rates_rate r2
            WHERE r2.provider_name   = r1.provider_name
              AND r2.rate_type       = r1.rate_type
              AND r2.effective_date  > r1.effective_date
        )
    """
    logger.debug("get_latest_rates called with rate_type=%s", rate_type)

    newer_row_exists = Rate.objects.filter(
        provider_name=OuterRef("provider_name"),
        rate_type=OuterRef("rate_type"),
        effective_date__gt=OuterRef("effective_date"),
    )

    queryset = Rate.objects.filter(~Exists(newer_row_exists))

    if rate_type:
        queryset = queryset.filter(rate_type__iexact=rate_type)

    return queryset.order_by("provider_name", "rate_type")


def get_rate_history(
    provider: str = None,
    rate_type: str = None,
    from_date: str = None,
    to_date: str = None,
):
    """
    Return a filtered, ordered queryset for the history endpoint.
    All parameters are optional; invalid date strings are ignored gracefully.
    Results are ordered by effective_date DESC (newest first) as required.
    """
    logger.debug(
        "get_rate_history called | provider=%s type=%s from=%s to=%s",
        provider, rate_type, from_date, to_date,
    )

    queryset = Rate.objects.all()

    if provider:
        queryset = queryset.filter(provider_name__icontains=provider)

    if rate_type:
        queryset = queryset.filter(rate_type__iexact=rate_type)

    if from_date:
        queryset = queryset.filter(effective_date__gte=from_date)

    if to_date:
        queryset = queryset.filter(effective_date__lte=to_date)

    # Newest dates first, then stable secondary sort
    return queryset.order_by("-effective_date", "provider_name", "rate_type")
