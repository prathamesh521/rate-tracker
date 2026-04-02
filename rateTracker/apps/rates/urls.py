from django.urls import path
from .views import LatestRatesView, RateHistoryView, RateIngestView

urlpatterns = [
    path("latest", LatestRatesView.as_view(), name="rates-latest"),
    path("history", RateHistoryView.as_view(), name="rates-history"),
    path("ingest", RateIngestView.as_view(), name="rates-ingest"),
]
