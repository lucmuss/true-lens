from django.core.management.base import BaseCommand

from apps.candidates.services import load_default_attributes


class Command(BaseCommand):
    help = "Seeds candidate attribute definitions from configured JSON file"

    def handle(self, *args, **options):
        load_default_attributes()
        self.stdout.write(self.style.SUCCESS("Attribute definitions synced."))
