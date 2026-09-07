from django.core.management.base import BaseCommand

from tenants.models import Tenant
from tenants.manager import migrate_tenant_database


class Command(BaseCommand):
    help = "Apply all migrations to all active tenant databases."

    def handle(self, *args, **options):
        tenants = Tenant.objects.using("default").filter(status="active")
        if not tenants.exists():
            self.stdout.write(self.style.WARNING("No active tenants found."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {tenants.count()} active tenant(s)."
            )
        )

        for tenant in tenants:
            self.stdout.write(
                f"\nMigrating tenant: {tenant.clinic_name} ({tenant.slug})..."
            )

            try:
                migrate_tenant_database(tenant)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {tenant.slug} migrated successfully."
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {tenant.slug} failed: {e}"
                    )
                )