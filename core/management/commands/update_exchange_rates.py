from django.conf import settings
from django.core.management import BaseCommand
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = 'Updates currency exchange rates'

    def handle(self, *args, **options):
        backend = settings.EXCHANGE_BACKEND
        backend = import_string(backend)()
        backend.update_rates()
