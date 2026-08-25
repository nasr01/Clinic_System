from copy import deepcopy

from django.conf import settings
from django.core.management import call_command
from django.db import connections


def configure_tenant_database(tenant):

    default_config = deepcopy(
        settings.DATABASES["default"]
    )

    default_config.update(
        {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": tenant.database_name,
            "USER": tenant.database_user,
            "PASSWORD": tenant.database_password,
            "HOST": tenant.database_host,
            "PORT": tenant.database_port,
        }
    )

    settings.DATABASES["tenant"] = default_config

    connections["tenant"].close()


def migrate_tenant_database(tenant):

    configure_tenant_database(tenant)

    call_command(
        "migrate",
        database="tenant",
        interactive=False,
        verbosity=1,
    )