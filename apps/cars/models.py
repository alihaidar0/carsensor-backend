from django.db import models


class Car(models.Model):
    # Identity
    external_id = models.CharField(max_length=100, unique=True)
    url = models.URLField(max_length=500)

    # Core fields
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=500)
    year = models.PositiveIntegerField()
    mileage = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_usd = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Details
    color = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(max_length=50, blank=True)
    transmission = models.CharField(max_length=50, blank=True)
    engine_size = models.CharField(max_length=20, blank=True)
    body_type = models.CharField(max_length=50, blank=True)
    drive_type = models.CharField(max_length=20, blank=True)
    doors = models.PositiveSmallIntegerField(null=True, blank=True)
    seats = models.PositiveSmallIntegerField(null=True, blank=True)
    inspection_date = models.CharField(max_length=50, blank=True)

    # Location
    location = models.CharField(max_length=100, blank=True)

    # Images
    image_url = models.URLField(max_length=500, blank=True)
    image_urls = models.JSONField(default=list)

    # Raw data
    raw_data = models.JSONField(default=dict)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scraped_at = models.DateTimeField()

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["brand", "model"]),
            models.Index(fields=["year"]),
            models.Index(fields=["price"]),
            models.Index(fields=["mileage"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.year} {self.brand} {self.model}"
