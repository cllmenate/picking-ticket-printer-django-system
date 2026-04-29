import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from environment variables (idempotent)"

    def handle(self, *args, **options):
        username = os.environ.get("SUPERUSER_USERNAME")
        email = os.environ.get("SUPERUSER_EMAIL")
        password = os.environ.get("SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stderr.write(
                self.style.ERROR(
                    "Missing required environment variables: "
                    "SUPERUSER_USERNAME, SUPERUSER_EMAIL, SUPERUSER_PASSWORD"
                )
            )
            return

        try:
            User.objects.filter(username=username).delete()
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(
                self.style.SUCCESS(f"Superuser '{username}' created successfully.")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to create superuser: {e}"))
