from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import connections
from getpass import getpass

from tenants.models import Tenant
from tenants.manager import configure_tenant_database, migrate_tenant_database
from tenants.routers import set_current_tenant_db, clear_current_tenant_db


class Command(BaseCommand):
    help = "Create a new clinic tenant with its own database"

    def add_arguments(self, parser):
        parser.add_argument("--clinic-name", required=True)
        parser.add_argument("--slug", required=True)
        parser.add_argument("--database-name", required=True)

        parser.add_argument(
            "--database-user",
            default="postgres",
        )

        parser.add_argument(
            "--database-host",
            default="127.0.0.1",
        )

        parser.add_argument(
            "--database-port",
            default=5432,
            type=int,
        )

        parser.add_argument("--database-password")

        parser.add_argument("--doctor-username")
        parser.add_argument("--doctor-name")
        parser.add_argument("--doctor-password")

    def handle(self, *args, **options):

        clinic_name = options["clinic_name"]
        slug = options["slug"]
        database_name = options["database_name"]

        database_user = options["database_user"]
        database_host = options["database_host"]
        database_port = options["database_port"]

        database_password = options["database_password"]

        if not database_password:
            database_password = getpass(
                "PostgreSQL password: "
            )

        doctor_username = options["doctor_username"]
        doctor_name = options["doctor_name"]
        doctor_password = options["doctor_password"]

        # --------------------------------------------------
        # Validate Tenant
        # --------------------------------------------------

        if Tenant.objects.using("default").filter(slug=slug).exists():
            raise CommandError(
                f"Tenant with slug '{slug}' already exists."
            )

        if Tenant.objects.using("default").filter(
            database_name=database_name
        ).exists():
            raise CommandError(
                f"Database '{database_name}' is already assigned."
            )

        # --------------------------------------------------
        # Create Tenant record in Control DB
        # --------------------------------------------------

        tenant = Tenant.objects.using("default").create(
            clinic_name=clinic_name,
            slug=slug,
            database_name=database_name,
            database_host=database_host,
            database_port=database_port,
            database_user=database_user,
            database_password=database_password,
            status=Tenant.Status.ACTIVE,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Tenant '{clinic_name}' created."
            )
        )

        try:
            # --------------------------------------------------
            # Configure Tenant DB
            # --------------------------------------------------

            configure_tenant_database(tenant)

            self.stdout.write(
                "Connecting to tenant database..."
            )

            connections["tenant"].ensure_connection()

            self.stdout.write(
                self.style.SUCCESS(
                    "Tenant database connection successful."
                )
            )

            # --------------------------------------------------
            # Run migrations
            # --------------------------------------------------

            self.stdout.write(
                "Running tenant migrations..."
            )

            migrate_tenant_database(tenant)

            self.stdout.write(
                self.style.SUCCESS(
                    "Tenant migrations completed."
                )
            )

            # --------------------------------------------------
            # Create Doctor
            # --------------------------------------------------

            if doctor_username:

                if not doctor_name:
                    raise CommandError(
                        "--doctor-name is required."
                    )

                if not doctor_password:
                    doctor_password = getpass(
                        "Doctor password: "
                    )

                set_current_tenant_db("tenant")

                try:
                    User = get_user_model()

                    doctor = User.objects.create_user(
                        username=doctor_username,
                        password=doctor_password,
                        full_name=doctor_name,
                        role=User.Role.DOCTOR,
                    )

                finally:
                    clear_current_tenant_db()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Doctor '{doctor.full_name}' created successfully."
                    )
                )

        except Exception as exc:

            # Remove Tenant record if setup failed
            Tenant.objects.using("default").filter(
                id=tenant.id
            ).delete()

            connections["tenant"].close()

            raise CommandError(
                f"Tenant setup failed: {exc}"
            )

        finally:
            connections["tenant"].close()

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Tenant setup completed successfully."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Clinic: {clinic_name}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Slug: {slug}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Database: {database_name}"
            )
        )