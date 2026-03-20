import django_filters
from .models import Car


class CarFilter(django_filters.FilterSet):
    year_min = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_max = django_filters.NumberFilter(field_name="year", lookup_expr="lte")
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    mileage_max = django_filters.NumberFilter(field_name="mileage", lookup_expr="lte")

    class Meta:
        model = Car
        fields = [
            "brand",
            "model",
            "fuel_type",
            "transmission",
            "body_type",
            "color",
            "location",
        ]
