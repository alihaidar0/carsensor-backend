import logging
from typing import Optional

from celery import shared_task
from django.db import transaction, IntegrityError

from apps.cars.models import Car
from .parser import scrape_all_cars

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.scraper.tasks.scrape_cars",
    # Auto-retry on unexpected exceptions (NOT on 403s — those are caught in parser)
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
    retry_backoff=True,
    acks_late=True,          # Only ACK after task completes — prevents silent loss on worker crash
    reject_on_worker_lost=True,
)
def scrape_cars() -> str:
    """
    Celery task: scrape carsensor.net and upsert all car listings to DB.

    Each car is upserted individually inside its own atomic savepoint.
    This means a single malformed record cannot roll back the entire batch —
    the rest of the scraped cars are still saved.
    """
    logger.info("Starting carsensor.net scrape task...")

    cars: list[dict] = scrape_all_cars()

    if not cars:
        logger.warning("Scraper returned zero cars. Check parser logs for 403 or selector errors.")
        return "No cars found"

    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0

    for car_data in cars:
        external_id: Optional[str] = car_data.pop("external_id", None)

        if not external_id:
            logger.warning(f"Skipping car with no external_id. Data: {car_data.get('url', 'unknown URL')}")
            skipped_count += 1
            continue

        # Use a savepoint per record so a single bad row doesn't abort the batch.
        # transaction.atomic() here creates a nested savepoint when called inside
        # an outer transaction, or a full transaction if called at the top level.
        try:
            with transaction.atomic():
                _, created = Car.objects.update_or_create(
                    external_id=external_id,
                    defaults=car_data,
                )
            if created:
                created_count += 1
            else:
                updated_count += 1

        except IntegrityError as exc:
            # Rare: race condition between two simultaneous scrape tasks.
            # The second worker will hit a unique constraint on external_id.
            logger.warning(f"IntegrityError for external_id={external_id}: {exc}")
            skipped_count += 1
        except Exception as exc:
            logger.error(
                f"Unexpected error upserting external_id={external_id}: {exc}",
                exc_info=True,
            )
            skipped_count += 1

    result = (
        f"Scrape complete — "
        f"created: {created_count}, "
        f"updated: {updated_count}, "
        f"skipped: {skipped_count}"
    )
    logger.info(result)
    return result
