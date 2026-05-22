"""
Seed development database with test recruiters and candidates.
Usage: uv run manage.py seed_dev_data
"""
from __future__ import annotations

import random
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.candidates.models import (
    Candidate,
    CandidateAttributeDefinition,
    CandidateAttributeVote,
    HairColor,
)

User = get_user_model()

_RECRUITERS = [
    {"email": "recruiter1@example.com", "display_name": "Alice Recruiter", "is_staff": False},
    {"email": "recruiter2@example.com", "display_name": "Bob Recruiter", "is_staff": False},
    {"email": "admin@example.com", "display_name": "Admin User", "is_staff": True, "is_superuser": True},
]

_CANDIDATES = [
    {
        "first_name": "Clara",
        "last_name": "Schmidt",
        "gender": "female",
        "birth_date": date(1990, 3, 4),
        "country": "Germany",
        "region": "Bayern",
        "city": "Munich",
        "hair_color": HairColor.BROWN,
        "primary_email": "clara.schmidt@example.com",
        "primary_phone": "+4915112345678",
    },
    {
        "first_name": "Max",
        "last_name": "Mueller",
        "gender": "male",
        "birth_date": date(1988, 7, 22),
        "country": "Germany",
        "region": "Berlin",
        "city": "Berlin",
        "hair_color": HairColor.BLACK,
        "primary_email": "max.mueller@example.com",
        "primary_phone": "+4917612345678",
    },
    {
        "first_name": "Laura",
        "last_name": "Weber",
        "gender": "female",
        "birth_date": date(1995, 11, 15),
        "country": "Germany",
        "region": "Nordrhein-Westfalen",
        "city": "Cologne",
        "hair_color": HairColor.BLONDE,
        "primary_email": "laura.weber@example.com",
        "primary_phone": "+4915987654321",
    },
    {
        "first_name": "Jonas",
        "last_name": "Fischer",
        "gender": "male",
        "birth_date": date(1993, 5, 8),
        "country": "Germany",
        "region": "Hessen",
        "city": "Frankfurt",
        "hair_color": HairColor.BROWN,
        "primary_email": "jonas.fischer@example.com",
        "primary_phone": "",
    },
    {
        "first_name": "Sophie",
        "last_name": "Bauer",
        "gender": "female",
        "birth_date": date(1998, 1, 30),
        "country": "Austria",
        "region": "Wien",
        "city": "Vienna",
        "hair_color": HairColor.RED,
        "primary_email": "sophie.bauer@example.com",
        "primary_phone": "+43664123456",
    },
]

DEFAULT_PASSWORD = "Test1234!secure"  # noqa: S105 – dev only


class Command(BaseCommand):
    help = "Seed development database with test recruiters and candidates"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing seed data first")

    def handle(self, *args, **options):
        if options["clear"]:
            User.objects.filter(email__in=[r["email"] for r in _RECRUITERS]).delete()
            Candidate.objects.filter(first_name__in=[c["first_name"] for c in _CANDIDATES]).delete()
            self.stdout.write(self.style.WARNING("Cleared existing seed data."))

        self._seed_recruiters()
        self._seed_candidates()
        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))

    def _seed_recruiters(self):
        for data in _RECRUITERS:
            email = data["email"]
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  Recruiter already exists: {email}")
                continue
            kwargs = {
                "email": email,
                "display_name": data.get("display_name", ""),
                "is_verified_recruiter": True,
                "is_staff": data.get("is_staff", False),
                "is_superuser": data.get("is_superuser", False),
                "credits": 10,
            }
            user = User(**kwargs)
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  Created recruiter: {email}"))

    def _seed_candidates(self):
        attrs = list(CandidateAttributeDefinition.objects.filter(is_active=True))
        recruiters = list(User.objects.filter(is_verified_recruiter=True, is_staff=False))

        for data in _CANDIDATES:
            if Candidate.objects.filter(
                first_name=data["first_name"], last_name=data["last_name"]
            ).exists():
                self.stdout.write(f"  Candidate already exists: {data['first_name']} {data['last_name']}")
                continue

            candidate = Candidate.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f"  Created candidate: {candidate}"))

            if attrs and recruiters:
                sample_attrs = random.sample(attrs, min(2, len(attrs)))
                recruiter = random.choice(recruiters)
                today = timezone.localdate()
                for attr in sample_attrs:
                    CandidateAttributeVote.objects.get_or_create(
                        candidate=candidate,
                        attribute=attr,
                        recruiter=recruiter,
                        defaults={"voted_on": today},
                    )
                candidate.distinct_recruiter_count = 1
                candidate.save(update_fields=["distinct_recruiter_count"])
