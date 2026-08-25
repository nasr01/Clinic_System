from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = (
        "Create a Platform Admin superuser in the control (default) database. "
        "This is an alias for: python manage.py create_platform_admin"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="Platform admin username (must be unique in default DB)",
        )
        parser.add_argument(
            "--full-name",
            default="",
            help="Optional display name",
        )
        parser.add_argument(
            "--password",
            help="Password (if omitted, prompted interactively)",
        )

    def handle(self, *args, **options):
        filtered = {
            "username": options.get("username"),
            "full_name": options.get("full_name"),
            "password": options.get("password"),
            "no_superuser": False,
            "inactive": False,
        }
        call_command("create_platform_admin", **filtered)
