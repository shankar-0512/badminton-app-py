import logging
from .models import history

logger = logging.getLogger(__name__)

def clear_history():
    count = history.objects.all().count()
    history.objects.all().delete()
    logger.info(f"Deleted {count} records from History model.")
