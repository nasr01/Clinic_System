from tenants.models import Tenant
from tenants.manager import configure_tenant_database
from tenants.routers import (
    set_current_tenant_db,
    clear_current_tenant_db,
)


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        tenant = None

        # =========================
        # 1. Try session
        # =========================

        tenant_id = None

        try:
            tenant_id = request.session.get("tenant_id")
        except Exception:
            try:
                request.session.flush()
            except Exception:
                pass

        if tenant_id:
            try:
                tenant = (
                    Tenant.objects
                    .using("default")
                    .get(
                        id=tenant_id,
                        status=Tenant.Status.ACTIVE,
                    )
                )
            except Tenant.DoesNotExist:
                tenant = None

        # =========================
        # 2. Try clinic_slug
        # =========================

        if tenant is None:

            clinic_slug = request.POST.get("clinic_slug")

            if not clinic_slug:
                clinic_slug = request.GET.get("clinic_slug")

            if clinic_slug:
                try:
                    tenant = (
                        Tenant.objects
                        .using("default")
                        .get(
                            slug=clinic_slug,
                            status=Tenant.Status.ACTIVE,
                        )
                    )
                except Tenant.DoesNotExist:
                    tenant = None

        # =========================
        # 3. Configure Tenant DB
        # =========================

        if tenant:
            configure_tenant_database(tenant)

            set_current_tenant_db("tenant")

            request.tenant = tenant

        else:
            clear_current_tenant_db()

            request.tenant = None

        # =========================
        # 4. Continue request
        # =========================

        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant_db()

        return response