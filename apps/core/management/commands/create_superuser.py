import os
import sys
import traceback

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from environment variables (idempotent)"

    def handle(self, *args, **options):
        print("Starting superuser creation...", flush=True)
        self.stdout.write("Starting superuser creation...")

        username = os.environ.get("SUPERUSER_USERNAME")
        email = os.environ.get("SUPERUSER_EMAIL")
        password = os.environ.get("SUPERUSER_PASSWORD")

        # Log which variables are present (never log the password value)
        print(f"SUPERUSER_USERNAME: {username!r}", flush=True)
        print(f"SUPERUSER_EMAIL: {email!r}", flush=True)
        print(f"SUPERUSER_PASSWORD: {'set' if password else 'NOT SET'}", flush=True)
        self.stdout.write(f"SUPERUSER_USERNAME: {username!r}")
        self.stdout.write(f"SUPERUSER_EMAIL: {email!r}")
        self.stdout.write(f"SUPERUSER_PASSWORD: {'set' if password else 'NOT SET'}")

        missing = [
            name
            for name, value in [
                ("SUPERUSER_USERNAME", username),
                ("SUPERUSER_EMAIL", email),
                ("SUPERUSER_PASSWORD", password),
            ]
            if not value
        ]

        if missing:
            msg = f"Missing required environment variable(s): {', '.join(missing)}"
            print(f"ERROR: {msg}", file=sys.stderr, flush=True)
            self.stderr.write(self.style.ERROR(msg))
            return

        try:
            print("Creating superuser...", flush=True)
            self.stdout.write("Creating superuser...")

            User.objects.filter(username=username).delete()
            User.objects.create_superuser(username=username, email=email, password=password)

            success_msg = f"Superuser '{username}' created successfully!"
            print(success_msg, flush=True)
            self.stdout.write(self.style.SUCCESS(success_msg))

        except Exception as e:
            error_msg = f"Failed to create superuser '{username}': {e}"
            print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            self.stderr.write(self.style.ERROR(error_msg))
