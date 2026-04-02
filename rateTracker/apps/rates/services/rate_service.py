import logging

from django.db.models import Exists, OuterRef

from apps.rates.models import Rate

logger = logging.getLogger(__name__)


def get_latest_rates(rate_type: str = None):
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
