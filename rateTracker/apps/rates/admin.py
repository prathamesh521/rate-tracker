from django.contrib import admin
from .models import Rate


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ("provider_name", "rate_type", "rate_value", "effective_date", "ingestion_timestamp")
    list_filter = ("rate_type", "provider_name")
    search_fields = ("provider_name", "rate_type")
    ordering = ("-effective_date",)
    date_hierarchy = "effective_date"
