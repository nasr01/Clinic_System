from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from tenants.manager import configure_tenant_database
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Repair missing patients.Patient file columns in tenant databases"

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            help="Repair a single tenant by slug (default: all tenants).",
        )

    def handle(self, *args, **options):
        slug = options.get("slug")

        qs = Tenant.objects.using("default").all().order_by("id")
        if slug:
            qs = qs.filter(slug=slug)

        if not qs.exists():
            raise CommandError("No tenants found for the given criteria.")

        for tenant in qs:
            self.stdout.write(
                f"\n==== TENANT: {tenant.slug} DB: {tenant.database_name} ===="
            )

            configure_tenant_database(tenant)

            conn = connections["tenant"]
            conn.close()
            conn.ensure_connection()

            missing = self._missing_columns(conn)

            if not missing:
                self.stdout.write(self.style.SUCCESS("OK (columns exist)"))
                conn.close()
                continue

            self.stdout.write(
                self.style.WARNING(
                    f"Missing columns on patients_patient: {', '.join(missing)}"
                )
            )

            call_command(
                "migrate",
                "patients",
                "0005",
                database="tenant",
                fake=True,
                interactive=False,
                verbosity=1,
            )

            call_command(
                "migrate",
                "patients",
                database="tenant",
                interactive=False,
                verbosity=1,
            )

            missing_after = self._missing_columns(conn)
            conn.close()

            if missing_after:
                raise CommandError(
                    f"Repair failed for tenant '{tenant.slug}'. Still missing: {', '.join(missing_after)}"
                )

            self.stdout.write(self.style.SUCCESS("Repaired successfully"))

    def _missing_columns(self, conn):
        expected = {"has_file", "file_created_at"}
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'patients_patient'
                  AND column_name IN ('has_file', 'file_created_at')
                """
            )
            existing = {row[0] for row in cursor.fetchall()}
        return sorted(expected - existing)

