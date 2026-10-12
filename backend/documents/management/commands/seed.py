"""Seed demo users, documents and a share so reviewers can test sharing.

Idempotent: safe to run repeatedly. Credentials are printed and documented in
the README. Passwords come from env vars in production (SEED_PASSWORD), with a
sane default for local review.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from documents.models import Document, Share
from documents.sanitize import sanitize_html

User = get_user_model()

DEFAULT_PASSWORD = os.environ.get("SEED_PASSWORD", "password123")

DEMO_USERS = [
    {"username": "alice", "email": "alice@example.com", "first_name": "Alice"},
    {"username": "bob", "email": "bob@example.com", "first_name": "Bob"},
    {"username": "carol", "email": "carol@example.com", "first_name": "Carol"},
]

WELCOME_HTML = sanitize_html(
    "<h1>Welcome to Ajaia Docs</h1>"
    "<p>This is a <strong>collaborative</strong> rich-text editor. Try "
    "<em>italic</em>, <u>underline</u>, and lists:</p>"
    "<ul><li>Create and rename documents</li>"
    "<li>Import a .txt or .md file</li>"
    "<li>Share with a teammate as viewer or editor</li></ul>"
    "<p>Edits autosave. Open a shared document to see access in action.</p>"
)

ROADMAP_HTML = sanitize_html(
    "<h2>Q3 Roadmap</h2>"
    "<ol><li>Ship document editor</li><li>Add sharing</li>"
    "<li>Gather feedback</li></ol>"
    "<blockquote>Prioritize depth over breadth.</blockquote>"
)


class Command(BaseCommand):
    help = "Create demo users, documents, and a share for review."

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "first_name": spec["first_name"],
                },
            )
            # Always (re)set the demo password so reviewers can log in.
            user.email = spec["email"]
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            users[spec["username"]] = user
            self.stdout.write(
                f"  {'created' if created else 'updated'} user {user.email}"
            )

        # Alice owns a welcome doc shared with Bob (editor) and Carol (viewer).
        welcome, _ = Document.objects.get_or_create(
            owner=users["alice"],
            title="Welcome to Ajaia Docs",
            defaults={"content": WELCOME_HTML},
        )
        Share.objects.update_or_create(
            document=welcome,
            user=users["bob"],
            defaults={"role": Share.Role.EDITOR, "created_by": users["alice"]},
        )
        Share.objects.update_or_create(
            document=welcome,
            user=users["carol"],
            defaults={"role": Share.Role.VIEWER, "created_by": users["alice"]},
        )

        # Bob owns a private roadmap (not shared) to show owned-vs-shared split.
        Document.objects.get_or_create(
            owner=users["bob"],
            title="Q3 Roadmap",
            defaults={"content": ROADMAP_HTML},
        )

        # Optionally create an admin for /admin/ if env vars provided.
        admin_user = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        admin_pass = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if admin_user and admin_pass:
            su, _ = User.objects.get_or_create(
                username=admin_user,
                defaults={"email": os.environ.get("DJANGO_SUPERUSER_EMAIL", "")},
            )
            su.is_staff = True
            su.is_superuser = True
            su.set_password(admin_pass)
            su.save()
            self.stdout.write(f"  ensured superuser {admin_user}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeed complete. Demo password: '{DEFAULT_PASSWORD}'\n"
                "Login emails: alice@example.com, bob@example.com, "
                "carol@example.com"
            )
        )
