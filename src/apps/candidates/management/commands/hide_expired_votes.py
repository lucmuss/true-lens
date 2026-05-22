from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.candidates.models import CandidateAttributeVote


class Command(BaseCommand):
    help = "Marks expired votes as not visible"

    def handle(self, *args, **options):
        today = timezone.localdate()
        count = CandidateAttributeVote.objects.filter(is_visible=True, expires_on__lte=today).update(is_visible=False)
        self.stdout.write(self.style.SUCCESS(f"Expired votes hidden: {count}"))
