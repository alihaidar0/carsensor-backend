from django.contrib import admin
from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "brand",
        "model",
        "year",
        "price",
        "mileage",
        "fuel_type",
        "location",
        "scraped_at",
    ]
    list_filter = ["brand", "fuel_type", "transmission", "body_type", "location"]
    search_fields = ["brand", "model", "external_id"]
    ordering = ["-scraped_at"]
