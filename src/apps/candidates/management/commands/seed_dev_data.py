"""
Seed development database with test recruiters and candidates.
Usage: uv run manage.py seed_dev_data
"""
from __future__ import annotations

import random
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.candidates.models import (
    Candidate,
    CandidateAttributeDefinition,
    CandidateAttributeVote,
    HairColor,
)

User = get_user_model()

_RECRUITERS = [
    {"email": "recruiter1@example.com", "display_name": "Alice Müller", "is_staff": False, "credits": 25},
    {"email": "recruiter2@example.com", "display_name": "Bob Wagner", "is_staff": False, "credits": 18},
    {"email": "recruiter3@example.com", "display_name": "Clara Hoffmann", "is_staff": False, "credits": 12},
    {"email": "recruiter4@example.com", "display_name": "David Schneider", "is_staff": False, "credits": 30},
    {"email": "recruiter5@example.com", "display_name": "Eva Becker", "is_staff": False, "credits": 8},
    {"email": "admin@example.com", "display_name": "Admin User", "is_staff": True, "is_superuser": True, "credits": 50},
]

_CANDIDATES = [
    # ── Bayern ────────────────────────────────────────────────────────────────
    {
        "first_name": "Clara",
        "last_name": "Schmidt",
        "gender": "female",
        "birth_date": date(1990, 3, 4),
        "country": "Germany",
        "region": "Bayern",
        "city": "München",
        "hair_color": HairColor.BROWN,
        "primary_email": "clara.schmidt@example.com",
        "primary_phone": "+4915112345678",
    },
    {
        "first_name": "Tobias",
        "last_name": "Huber",
        "gender": "male",
        "birth_date": date(1987, 9, 12),
        "country": "Germany",
        "region": "Bayern",
        "city": "Augsburg",
        "hair_color": HairColor.BLONDE,
        "primary_email": "tobias.huber@example.com",
        "primary_phone": "+4915245678901",
    },
    {
        "first_name": "Lena",
        "last_name": "Maier",
        "gender": "female",
        "birth_date": date(1996, 6, 18),
        "country": "Germany",
        "region": "Bayern",
        "city": "Nürnberg",
        "hair_color": HairColor.RED,
        "primary_email": "lena.maier@example.com",
        "primary_phone": "+4916112233445",
    },
    # ── Berlin ────────────────────────────────────────────────────────────────
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
        "first_name": "Nina",
        "last_name": "Koch",
        "gender": "female",
        "birth_date": date(1994, 2, 28),
        "country": "Germany",
        "region": "Berlin",
        "city": "Berlin",
        "hair_color": HairColor.BROWN,
        "primary_email": "nina.koch@example.com",
        "primary_phone": "+4915511223344",
    },
    {
        "first_name": "Fabian",
        "last_name": "Richter",
        "gender": "male",
        "birth_date": date(1991, 11, 5),
        "country": "Germany",
        "region": "Berlin",
        "city": "Berlin",
        "hair_color": HairColor.BROWN,
        "primary_email": "fabian.richter@example.com",
        "primary_phone": "",
    },
    # ── Nordrhein-Westfalen ───────────────────────────────────────────────────
    {
        "first_name": "Laura",
        "last_name": "Weber",
        "gender": "female",
        "birth_date": date(1995, 11, 15),
        "country": "Germany",
        "region": "Nordrhein-Westfalen",
        "city": "Köln",
        "hair_color": HairColor.BLONDE,
        "primary_email": "laura.weber@example.com",
        "primary_phone": "+4915987654321",
    },
    {
        "first_name": "Stefan",
        "last_name": "Klein",
        "gender": "male",
        "birth_date": date(1985, 4, 3),
        "country": "Germany",
        "region": "Nordrhein-Westfalen",
        "city": "Düsseldorf",
        "hair_color": HairColor.GRAY,
        "primary_email": "stefan.klein@example.com",
        "primary_phone": "+4917899887766",
    },
    {
        "first_name": "Mia",
        "last_name": "Wolf",
        "gender": "female",
        "birth_date": date(1999, 8, 20),
        "country": "Germany",
        "region": "Nordrhein-Westfalen",
        "city": "Dortmund",
        "hair_color": HairColor.BLACK,
        "primary_email": "mia.wolf@example.com",
        "primary_phone": "+4916011223344",
    },
    # ── Hessen ────────────────────────────────────────────────────────────────
    {
        "first_name": "Jonas",
        "last_name": "Fischer",
        "gender": "male",
        "birth_date": date(1993, 5, 8),
        "country": "Germany",
        "region": "Hessen",
        "city": "Frankfurt am Main",
        "hair_color": HairColor.BROWN,
        "primary_email": "jonas.fischer@example.com",
        "primary_phone": "",
    },
    {
        "first_name": "Sophia",
        "last_name": "Zimmermann",
        "gender": "female",
        "birth_date": date(1992, 12, 1),
        "country": "Germany",
        "region": "Hessen",
        "city": "Wiesbaden",
        "hair_color": HairColor.BLONDE,
        "primary_email": "sophia.zimmermann@example.com",
        "primary_phone": "+4915344556677",
    },
    # ── Baden-Württemberg ─────────────────────────────────────────────────────
    {
        "first_name": "Lukas",
        "last_name": "Braun",
        "gender": "male",
        "birth_date": date(1989, 3, 17),
        "country": "Germany",
        "region": "Baden-Württemberg",
        "city": "Stuttgart",
        "hair_color": HairColor.BROWN,
        "primary_email": "lukas.braun@example.com",
        "primary_phone": "+4916388990011",
    },
    {
        "first_name": "Hannah",
        "last_name": "Krause",
        "gender": "female",
        "birth_date": date(1997, 7, 9),
        "country": "Germany",
        "region": "Baden-Württemberg",
        "city": "Freiburg im Breisgau",
        "hair_color": HairColor.RED,
        "primary_email": "hannah.krause@example.com",
        "primary_phone": "+4915677889900",
    },
    # ── Hamburg ───────────────────────────────────────────────────────────────
    {
        "first_name": "Tim",
        "last_name": "Schulz",
        "gender": "male",
        "birth_date": date(1986, 10, 25),
        "country": "Germany",
        "region": "Hamburg",
        "city": "Hamburg",
        "hair_color": HairColor.BLONDE,
        "primary_email": "tim.schulz@example.com",
        "primary_phone": "+4917222334455",
    },
    {
        "first_name": "Julia",
        "last_name": "Neumann",
        "gender": "female",
        "birth_date": date(1993, 1, 14),
        "country": "Germany",
        "region": "Hamburg",
        "city": "Hamburg",
        "hair_color": HairColor.BROWN,
        "primary_email": "julia.neumann@example.com",
        "primary_phone": "+4915844556677",
    },
    # ── Sachsen ───────────────────────────────────────────────────────────────
    {
        "first_name": "Kevin",
        "last_name": "Hartmann",
        "gender": "male",
        "birth_date": date(1990, 6, 30),
        "country": "Germany",
        "region": "Sachsen",
        "city": "Leipzig",
        "hair_color": HairColor.BLACK,
        "primary_email": "kevin.hartmann@example.com",
        "primary_phone": "+4917611223344",
    },
    {
        "first_name": "Anna",
        "last_name": "Lange",
        "gender": "female",
        "birth_date": date(1998, 4, 22),
        "country": "Germany",
        "region": "Sachsen",
        "city": "Dresden",
        "hair_color": HairColor.BLONDE,
        "primary_email": "anna.lange@example.com",
        "primary_phone": "+4915933445566",
    },
    # ── Austria ───────────────────────────────────────────────────────────────
    {
        "first_name": "Sophie",
        "last_name": "Bauer",
        "gender": "female",
        "birth_date": date(1998, 1, 30),
        "country": "Austria",
        "region": "Wien",
        "city": "Wien",
        "hair_color": HairColor.RED,
        "primary_email": "sophie.bauer@example.com",
        "primary_phone": "+43664123456",
    },
    {
        "first_name": "Markus",
        "last_name": "Gruber",
        "gender": "male",
        "birth_date": date(1984, 8, 16),
        "country": "Austria",
        "region": "Steiermark",
        "city": "Graz",
        "hair_color": HairColor.BROWN,
        "primary_email": "markus.gruber@example.com",
        "primary_phone": "+43676987654",
    },
    {
        "first_name": "Lisa",
        "last_name": "Hofer",
        "gender": "female",
        "birth_date": date(1995, 3, 11),
        "country": "Austria",
        "region": "Tirol",
        "city": "Innsbruck",
        "hair_color": HairColor.BLONDE,
        "primary_email": "lisa.hofer@example.com",
        "primary_phone": "+43650556677",
    },
    # ── Switzerland ───────────────────────────────────────────────────────────
    {
        "first_name": "Raphael",
        "last_name": "Meier",
        "gender": "male",
        "birth_date": date(1991, 5, 27),
        "country": "Switzerland",
        "region": "Zürich",
        "city": "Zürich",
        "hair_color": HairColor.BLACK,
        "primary_email": "raphael.meier@example.com",
        "primary_phone": "+41791234567",
    },
    {
        "first_name": "Katrin",
        "last_name": "Müller",
        "gender": "female",
        "birth_date": date(1989, 9, 3),
        "country": "Switzerland",
        "region": "Bern",
        "city": "Bern",
        "hair_color": HairColor.BROWN,
        "primary_email": "katrin.mueller@example.com",
        "primary_phone": "+41796543210",
    },
    {
        "first_name": "Patrick",
        "last_name": "Keller",
        "gender": "male",
        "birth_date": date(1996, 12, 8),
        "country": "Switzerland",
        "region": "Basel-Stadt",
        "city": "Basel",
        "hair_color": HairColor.BLONDE,
        "primary_email": "patrick.keller@example.com",
        "primary_phone": "",
    },
    {
        "first_name": "Michelle",
        "last_name": "Steiner",
        "gender": "female",
        "birth_date": date(1993, 7, 19),
        "country": "Switzerland",
        "region": "Genf",
        "city": "Genf",
        "hair_color": HairColor.OTHER,
        "primary_email": "michelle.steiner@example.com",
        "primary_phone": "+41781234560",
    },
]

class Command(BaseCommand):
    help = "Seed development database with test recruiters and candidates"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing seed data first")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow execution even when DEBUG is disabled.",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="",
            help="Optional shared password for all created recruiters (not recommended for public environments).",
        )
        parser.add_argument(
            "--random-password-length",
            type=int,
            default=24,
            help="Password length used when --password is not provided (minimum 12).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("seed_dev_data is blocked in production-like mode. Use --force explicitly.")

        self._password_override = (options.get("password") or "").strip() or None
        self._random_password_length = max(12, int(options.get("random_password_length") or 24))
        self._created_credentials: list[tuple[str, str]] = []

        if options["clear"]:
            User.objects.filter(email__in=[r["email"] for r in _RECRUITERS]).delete()
            Candidate.objects.filter(first_name__in=[c["first_name"] for c in _CANDIDATES]).delete()
            self.stdout.write(self.style.WARNING("Cleared existing seed data."))

        self._seed_recruiters()
        self._seed_candidates()
        if self._created_credentials:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Created recruiter credentials (store temporarily and rotate):"))
            for email, password in self._created_credentials:
                self.stdout.write(f"  {email} / {password}")
        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))

    def _seed_recruiters(self):
        for data in _RECRUITERS:
            email = data["email"]
            password = self._password_override or get_random_string(self._random_password_length)
            existing = User.objects.filter(email=email).first()
            if existing:
                if self._password_override:
                    existing.set_password(password)
                    existing.save(update_fields=["password"])
                    self.stdout.write(f"  Reset password: {email}")
                else:
                    self.stdout.write(f"  Recruiter already exists: {email}")
                continue
            user = User(
                email=email,
                display_name=data.get("display_name", ""),
                is_verified_recruiter=True,
                is_staff=data.get("is_staff", False),
                is_superuser=data.get("is_superuser", False),
                credits=data.get("credits", 10),
            )
            user.set_password(password)
            user.save()
            self._created_credentials.append((email, password))
            self.stdout.write(self.style.SUCCESS(f"  Created recruiter: {email}"))

    def _seed_candidates(self):
        attrs = list(CandidateAttributeDefinition.objects.filter(is_active=True))
        recruiters = list(User.objects.filter(is_verified_recruiter=True, is_staff=False))
        today = timezone.localdate()

        for data in _CANDIDATES:
            if Candidate.objects.filter(
                first_name=data["first_name"], last_name=data["last_name"]
            ).exists():
                self.stdout.write(f"  Candidate already exists: {data['first_name']} {data['last_name']}")
                continue

            candidate = Candidate.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f"  Created candidate: {candidate}"))

            if not attrs or not recruiters:
                continue

            # Spread votes across 1-4 recruiters for realistic vote counts
            num_voters = random.randint(1, min(4, len(recruiters)))
            voting_recruiters = random.sample(recruiters, num_voters)
            distinct = 0

            for recruiter in voting_recruiters:
                # Each recruiter votes on 1-3 random attributes
                sample_attrs = random.sample(attrs, random.randint(1, min(3, len(attrs))))
                voted = False
                for attr in sample_attrs:
                    _, created = CandidateAttributeVote.objects.get_or_create(
                        candidate=candidate,
                        attribute=attr,
                        recruiter=recruiter,
                        defaults={"voted_on": today},
                    )
                    if created:
                        voted = True
                if voted:
                    distinct += 1

            # Simulate some profile views
            candidate.profile_views_count = random.randint(3, 40)
            candidate.distinct_recruiter_count = distinct
            candidate.save(update_fields=["profile_views_count", "distinct_recruiter_count"])
