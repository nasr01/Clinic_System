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
    يحدد أي App يشتغل على Control DB
    وأي App يشتغل على Tenant DB.
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
            return get_current_tenant_db()

        return None

    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label

        if app_label in self.DEFAULT_ONLY_APPS:
            return "default"

        if app_label in self.SHARED_APPS:
            tenant_db = get_current_tenant_db()
            return tenant_db if tenant_db else "default"

        if app_label in self.TENANT_ONLY_APPS:
            return get_current_tenant_db()

        return None

    def allow_relation(self, obj1, obj2, **hints):
        db1 = obj1._state.db
        db2 = obj2._state.db

        if db1 and db2:
            return db1 == db2

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):

        if db == "default":
            if app_label in self.DEFAULT_ONLY_APPS:
                return True
            if app_label in self.SHARED_APPS:
                return True
            if app_label in self.TENANT_ONLY_APPS:
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