from rest_framework import serializers
from .models import Car


class CarListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            "id",
            "brand",
            "model",
            "year",
            "mileage",
            "price",
            "color",
            "fuel_type",
            "transmission",
            "body_type",
            "location",
            "image_url",
            "scraped_at",
        ]


class CarDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            "id",
            "external_id",
            "url",
            "brand",
            "model",
            "year",
            "mileage",
            "price",
            "price_usd",
            "color",
            "fuel_type",
            "transmission",
            "engine_size",
            "body_type",
            "drive_type",
            "doors",
            "seats",
            "inspection_date",
            "location",
            "image_url",
            "image_urls",
            "created_at",
            "scraped_at",
        ]
