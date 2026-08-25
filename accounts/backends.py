from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from tenants.routers import get_current_tenant_db

class TenantModelBackend(ModelBackend):


  def authenticate(
    self,
    request,
    username=None,
    password=None,
    **kwargs,
):
    if username is None:
        username = kwargs.get(
            get_user_model().USERNAME_FIELD
        )

    if username is None or password is None:
        return None

    tenant_db = get_current_tenant_db()

    # No tenant selected yet.
    # Do not query accounts_user from the default DB.
    if not tenant_db:
        return None

    UserModel = get_user_model()

    try:
        user = (
            UserModel._default_manager
            .using(tenant_db)
            .get(username=username)
        )
    except UserModel.DoesNotExist:
        return None

    if (
        user.check_password(password)
        and self.user_can_authenticate(user)
    ):
        return user

    return None

  def get_user(self, user_id):
    tenant_db = get_current_tenant_db()

    # No tenant selected.
    # Never query accounts_user from the control DB.
    if not tenant_db:
        return None

    UserModel = get_user_model()

    try:
        return (
            UserModel._default_manager
            .using(tenant_db)
            .get(pk=user_id)
        )
    except UserModel.DoesNotExist:
        return None

