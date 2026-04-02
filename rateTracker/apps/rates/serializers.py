from rest_framework import serializers
from .models import Rate


class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = [
            "id",
            "provider_name",
            "rate_type",
            "rate_value",
            "effective_date",
            "ingestion_timestamp",
        ]


class RateIngestSerializer(serializers.Serializer):
    provider_name = serializers.CharField(max_length=255)
    rate_type = serializers.CharField(max_length=100)
    rate_value = serializers.FloatField()
    effective_date = serializers.DateField()

    def validate_provider_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("provider_name cannot be blank.")
        return stripped

    def validate_rate_type(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("rate_type cannot be blank.")
        return stripped

    def validate_rate_value(self, value):
        if value < 0:
            raise serializers.ValidationError("rate_value must be non-negative.")
        return value
