from rest_framework import generics
from .models import Car
from .serializers import CarListSerializer, CarDetailSerializer
from .filters import CarFilter


class CarListView(generics.ListAPIView):
    queryset = Car.objects.all()
    serializer_class = CarListSerializer
    filterset_class = CarFilter
    ordering_fields = ["price", "year", "mileage", "created_at"]
    ordering = ["-scraped_at"]


class CarDetailView(generics.RetrieveAPIView):
    queryset = Car.objects.all()
    serializer_class = CarDetailSerializer
