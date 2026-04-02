import logging

from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rates.serializers import RateIngestSerializer, RateSerializer
from apps.rates.services import ingestion_service, rate_service

logger = logging.getLogger(__name__)

RATES_CACHE_TTL = 60  # seconds
_CACHE_VERSION_KEY = "rates:cache:version"


def _latest_cache_key(rate_type: str | None) -> str:
    version = cache.get(_CACHE_VERSION_KEY, 1)
    return f"rates:latest:v{version}:{rate_type or 'all'}"


def _invalidate_rates_cache() -> None:
    version = cache.get(_CACHE_VERSION_KEY, 1)
    cache.set(_CACHE_VERSION_KEY, version + 1, timeout=None)
    logger.info("Rates cache invalidated (version → %d)", version + 1)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class RatePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500


# ---------------------------------------------------------------------------
# GET /rates/latest
# ---------------------------------------------------------------------------

class LatestRatesView(APIView):
    def get(self, request):
        rate_type = request.query_params.get("type", "").strip().lower() or None
        cache_key = _latest_cache_key(rate_type)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug("Cache hit: %s", cache_key)
            return Response(cached_data)

        try:
            rates = rate_service.get_latest_rates(rate_type=rate_type)
            serializer = RateSerializer(rates, many=True)
            data = serializer.data
            cache.set(cache_key, data, RATES_CACHE_TTL)
            logger.debug("Cache populated: %s (%d records)", cache_key, len(data))
            return Response(data)
        except Exception as exc:
            logger.exception("Error in LatestRatesView: %s", exc)
            return Response(
                {"error": "Unable to retrieve latest rates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# GET /rates/history
# ---------------------------------------------------------------------------

class RateHistoryView(generics.ListAPIView):
    serializer_class = RateSerializer
    pagination_class = RatePagination

    def get_queryset(self):
        params = self.request.query_params
        return rate_service.get_rate_history(
            provider=params.get("provider"),
            rate_type=params.get("type"),
            from_date=params.get("from"),
            to_date=params.get("to"),
        )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Error in RateHistoryView: %s", exc)
            return Response(
                {"error": "Unable to retrieve rate history."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# POST /rates/ingest
# ---------------------------------------------------------------------------

class RateIngestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RateIngestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("RateIngestView validation failed: %s", serializer.errors)
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rate, created = ingestion_service.save_single_rate(serializer.validated_data)
            _invalidate_rates_cache()
            response_data = RateSerializer(rate).data
            http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(response_data, status=http_status)
        except Exception as exc:
            logger.exception("Error in RateIngestView: %s", exc)
            return Response(
                {"error": "Failed to save rate record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
