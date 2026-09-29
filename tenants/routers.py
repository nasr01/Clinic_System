from threading import local


_thread_locals = local()


def set_current_tenant_db(db_alias):
    _thread_locals.tenant_db = db_alias


def get_current_tenant_db():
    return getattr(_thread_locals, "tenant_db", None)


def clear_current_tenant_db():
    if hasattr(_thread_locals, "tenant_db"):
        del _thread_locals.tenant_db


class TenantDatabaseRouter:
    """
    Routes database operations to either control DB or tenant DB.
    SECURITY: Tenant-only apps MUST NOT operate without tenant context.
    """

    DEFAULT_ONLY_APPS = {
        "tenants",
        "sessions",
        "admin",
    }

    SHARED_APPS = {
        "auth",
        "contenttypes",
    }

    TENANT_ONLY_APPS = {
        "accounts",
        "patients",
    }

    def db_for_read(self, model, **hints):
        app_label = model._meta.app_label

        if app_label in self.DEFAULT_ONLY_APPS:
            return "default"

        if app_label in self.SHARED_APPS:
            tenant_db = get_current_tenant_db()
            return tenant_db if tenant_db else "default"

        if app_label in self.TENANT_ONLY_APPS:
            tenant_db = get_current_tenant_db()
            # SECURITY: Fail closed - never allow tenant apps on default DB
            if not tenant_db:
                raise RuntimeError(
                    f"SECURITY: Attempted to read {app_label}.{model.__name__} "
                    "without tenant context. This could expose cross-tenant data."
                )
            return tenant_db

        return None

    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label

        if app_label in self.DEFAULT_ONLY_APPS:
            return "default"

        if app_label in self.SHARED_APPS:
            tenant_db = get_current_tenant_db()
            return tenant_db if tenant_db else "default"

        if app_label in self.TENANT_ONLY_APPS:
            tenant_db = get_current_tenant_db()
            # SECURITY: Fail closed - never allow tenant apps on default DB
            if not tenant_db:
                raise RuntimeError(
                    f"SECURITY: Attempted to write {app_label}.{model.__name__} "
                    "without tenant context. This could cause data corruption."
                )
            return tenant_db

        return None

    def allow_relation(self, obj1, obj2, **hints):
        db1 = obj1._state.db
        db2 = obj2._state.db

        if db1 and db2:
            return db1 == db2

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # During tests, the test database name will be test_clinic_saas
        # We need to allow migrations for both default and tenant apps
        # to avoid foreign key issues during admin migrations
        is_test_db = db.startswith('test_') or db == 'default'
        
        if db == "default" or (is_test_db and db not in ["tenant"]):
            if app_label in self.DEFAULT_ONLY_APPS:
                return True
            if app_label in self.SHARED_APPS:
                return True
            if app_label in self.TENANT_ONLY_APPS:
                # During tests, allow tenant apps in default to avoid FK issues
                # In production, tenant apps should never be in default
                if 'test' in db or db == 'default':
                    # Check if we're in a test environment
                    import sys
                    if 'test' in sys.argv:
                        return True
                return False
            return None

        if db == "tenant":
            if app_label in self.DEFAULT_ONLY_APPS:
                return False
            if app_label in self.SHARED_APPS:
                return True
            if app_label in self.TENANT_ONLY_APPS:
                return True
            return None

        return None