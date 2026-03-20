import factory
from django.utils import timezone
from .models import Car


class CarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Car

    external_id = factory.Sequence(lambda n: f"CS{n:06d}")
    url = factory.Sequence(lambda n: f"https://carsensor.net/usedcar/CS{n:06d}/")
    brand = factory.Iterator(["Toyota", "Honda", "Nissan", "Mazda", "Subaru"])
    model = factory.Iterator(["Prius", "Fit", "Note", "CX-5", "Forester"])
    year = factory.Iterator([2018, 2019, 2020, 2021, 2022, 2023])
    mileage = factory.Faker("random_int", min=1000, max=100000)
    price = factory.Faker("pydecimal", left_digits=7, right_digits=2, positive=True)
    color = factory.Iterator(["White", "Black", "Silver", "Gray", "Blue"])
    fuel_type = factory.Iterator(["Gasoline", "Hybrid", "Electric"])
    transmission = factory.Iterator(["AT", "CVT", "MT"])
    body_type = factory.Iterator(["Sedan", "SUV", "Compact", "Wagon"])
    location = factory.Iterator(["Tokyo", "Osaka", "Aichi", "Kanagawa"])
    image_url = factory.Faker("image_url")
    image_urls = factory.LazyAttribute(lambda o: [o.image_url])
    raw_data = factory.LazyFunction(dict)
    scraped_at = factory.LazyFunction(timezone.now)
