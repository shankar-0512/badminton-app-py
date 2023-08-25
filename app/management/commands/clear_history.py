from django.core.management.base import BaseCommand
from app.models import history

class Command(BaseCommand):
    help = 'Clears the history table'

    def handle(self, *args, **kwargs):
        # Deleting all records from the history table
        history.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared the history table!'))
