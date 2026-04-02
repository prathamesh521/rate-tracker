import logging
from django.db import models

logger = logging.getLogger(__name__)


class Rate(models.Model):
    """
    Stores interest rate data per provider, type, and effective date.
    The unique constraint on (provider_name, rate_type, effective_date)
    ensures idempotent ingestion — no duplicate rows per day.
    """
    provider_name = models.CharField(max_length=255)
    rate_type = models.CharField(max_length=100)
    rate_value = models.FloatField()
    effective_date = models.DateField()
    ingestion_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider_name", "rate_type", "effective_date"],
                name="unique_rate_provider_type_date",
            )
        ]
        indexes = [
            # Covers most API query patterns
            models.Index(fields=["provider_name", "rate_type", "effective_date"]),
            models.Index(fields=["effective_date"]),
            models.Index(fields=["rate_type"]),
        ]
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.provider_name} | {self.rate_type} | {self.effective_date} | {self.rate_value}"
