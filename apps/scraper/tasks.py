import logging
from celery import shared_task
from django.utils import timezone
from apps.cars.models import Car
from .parser import scrape_all_cars

logger = logging.getLogger(__name__)


@shared_task(name="apps.scraper.tasks.scrape_cars")
def scrape_cars():
    logger.info("Starting carsensor.net scrape...")
    cars = scrape_all_cars()

    if not cars:
        logger.warning("No cars scraped.")
        return "No cars found"

    created_count = 0
    updated_count = 0

    for car_data in cars:
        external_id = car_data.pop("external_id", None)
        if not external_id:
            continue
        _, created = Car.objects.update_or_create(
            external_id=external_id,
            defaults=car_data,
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    result = f"Scrape complete: {created_count} created, {updated_count} updated"
    logger.info(result)
    return result
