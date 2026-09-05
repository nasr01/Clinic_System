from django.http import HttpResponse

from tenants.models import Tenant
from tenants.manager import configure_tenant_database
from tenants.routers import (
    set_current_tenant_db,
    clear_current_tenant_db,
)


def _extract_slug_from_host(request):
    try:
        host = request.get_host() or ""
    except Exception:
        return None

    if ":" in host:
        host = host.rsplit(":", 1)[0]

    if not host:
        return None

    parts = host.split(".")

    if not parts or parts[0] == "":
        return None

    if all(p.isdigit() for p in parts):
        return None

    if len(parts) == 1 and parts[0].lower() == "localhost":
        return None

    if len(parts) >= 2:
        slug = parts[0]
        if slug and slug.lower() != "localhost":
            return slug

    return None


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        is_admin_path = request.path.startswith("/admin/")

        if is_admin_path:
            clear_current_tenant_db()
            request.tenant = None
            try:
                response = self.get_response(request)
            finally:
                clear_current_tenant_db()
            return response

        slug_from_host = _extract_slug_from_host(request)

        tenant = None

        if slug_from_host:
            try:
                tenant = (
                    Tenant.objects
                    .using("default")
                    .get(
                        slug=slug_from_host,
                        status=Tenant.Status.ACTIVE,
                    )
                )
            except Tenant.DoesNotExist:
                tenant = None

        if tenant is None:
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

        if tenant is None:
            clear_current_tenant_db()
            request.tenant = None

            if slug_from_host:
                message = "رابط العيادة غير صحيح أو العيادة غير موجودة."
            else:
                message = "يرجى الدخول من رابط العيادة الصحيح."

            html = (
                "<!DOCTYPE html>\n"
                "<html lang='ar' dir='rtl'>\n"
                "<head>\n"
                "  <meta charset='UTF-8' />\n"
                "  <title>خطأ في العيادة</title>\n"
                "  <style>\n"
                "    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }\n"
                "    .card { background: #fff; padding: 48px 40px; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 520px; width: 90%; text-align: center; }\n"
                "    .icon { width: 72px; height: 72px; margin: 0 auto 20px; border-radius: 50%; background: #fef2f2; display: flex; align-items: center; justify-content: center; color: #dc2626; font-size: 36px; }\n"
                "    h1 { color: #1e293b; margin: 0 0 12px; font-size: 24px; }\n"
                "    p { color: #64748b; font-size: 16px; margin: 0; line-height: 1.6; }\n"
                "  </style>\n"
                "</head>\n"
                "<body>\n"
                "  <div class='card'>\n"
                "    <div class='icon'>!</div>\n"
                f"    <h1>{message}</h1>\n"
                "  </div>\n"
                "</body>\n"
                "</html>\n"
            )
            return HttpResponse(
                html,
                content_type="text/html; charset=utf-8",
                status=400,
            )

        configure_tenant_database(tenant)
        set_current_tenant_db("tenant")
        request.tenant = tenant

        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant_db()

        return response
