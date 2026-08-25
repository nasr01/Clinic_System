from django.contrib.auth.backends import BaseBackend
from django.utils import timezone

from .models import PlatformAdmin
from .routers import get_current_tenant_db


class PlatformAdminBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        tenant_db = get_current_tenant_db()
        if tenant_db:
            return None

        if username is None or password is None:
            return None

        try:
            user = PlatformAdmin.objects.using("default").get(
                username=username,
                is_active=True,
                is_staff=True,
            )
        except PlatformAdmin.DoesNotExist:
            return None

        if user.check_password(password):
            user.last_login = timezone.now()
            user.save(using="default", update_fields=["last_login"])
            return user

        return None

    def get_user(self, user_id):
        tenant_db = get_current_tenant_db()
        if tenant_db:
            return None

        try:
            return PlatformAdmin.objects.using("default").get(pk=user_id)
        except PlatformAdmin.DoesNotExist:
            return None
