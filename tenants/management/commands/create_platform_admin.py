from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from tenants.models import PlatformAdmin


class Command(BaseCommand):
    help = (
        "Create a Platform Admin account in the control (default) database. "
        "Platform admins are stored SEPARATELY from tenant accounts.User and "
        "live exclusively in the default database."
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
        parser.add_argument(
            "--no-superuser",
            action="store_true",
            default=False,
            help="Create the admin WITHOUT the is_superuser flag",
        )
        parser.add_argument(
            "--inactive",
            action="store_true",
            default=False,
            help="Create the admin with is_active=False",
        )

    def handle(self, *args, **options):

        username = options.get("username")
        if not username:
            username = input("Platform admin username: ").strip()
        if not username:
            raise CommandError("A username is required.")

        username = username.strip()

        full_name = (options.get("full_name") or "").strip()

        password = options.get("password")
        if not password:
            password = getpass("Platform admin password: ")
            if not password:
                raise CommandError("A password is required.")
            password_confirm = getpass("Confirm password: ")
            if password != password_confirm:
                raise CommandError("Passwords do not match.")

        is_active = not bool(options.get("inactive"))
        is_superuser = not bool(options.get("no_superuser"))

        # --------------------------------------------------
        # Uniqueness check against default DB only
        # --------------------------------------------------
        if (
            PlatformAdmin.objects
            .using("default")
            .filter(username=username)
            .exists()
        ):
            raise CommandError(
                f"Platform admin with username '{username}' already exists "
                "in the default database."
            )

        # --------------------------------------------------
        # Build & save (always explicitly using="default")
        # --------------------------------------------------
        admin = PlatformAdmin(
            username=username,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        admin.set_password(password)
        admin.save(using="default")

        # --------------------------------------------------
        # Verify the record landed in the default database
        # --------------------------------------------------
        verify = (
            PlatformAdmin.objects
            .using("default")
            .get(pk=admin.pk)
        )
        if not verify.check_password(password):
            raise CommandError(
                "Password verification failed after save."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "================================================"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Platform admin created successfully."
            )
        )
        self.stdout.write(
            f"  Database        : default (control DB)"
        )
        self.stdout.write(
            f"  Model           : tenants.PlatformAdmin"
        )
        self.stdout.write(
            f"  Primary key     : {verify.pk}"
        )
        self.stdout.write(
            f"  Username        : {verify.username}"
        )
        self.stdout.write(
            f"  Full name       : {verify.full_name or '-'} (saved: {bool(verify.full_name)})"
        )
        self.stdout.write(
            f"  is_active       : {verify.is_active}"
        )
        self.stdout.write(
            f"  is_superuser    : {verify.is_superuser}"
        )
        self.stdout.write(
            f"  password_hash   : {verify.password[:24]}..."
        )
        self.stdout.write(
            f"  created_at      : {verify.created_at.isoformat()}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                "================================================"
            )
        )
