from django import forms
from django.contrib import admin, messages
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.models import LogEntryManager
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import IntegrityError

from .models import Tenant
from .database import (
    create_tenant_database,
    validate_database_name,
)
from .manager import (
    configure_tenant_database,
    migrate_tenant_database,
)
from .routers import (
    set_current_tenant_db,
    clear_current_tenant_db,
)


def _patched_build_recent_actions(self, user, limit=10):
    return []


AdminSite._build_recent_actions = _patched_build_recent_actions


def _patched_get_admin_log(self, *args, **kwargs):
    return self.none()


LogEntryManager.get_admin_log = _patched_get_admin_log


_original_each_context = AdminSite.each_context


def _patched_each_context(self, request):
    ctx = _original_each_context(self, request)
    ctx["recent_actions"] = []
    return ctx


AdminSite.each_context = _patched_each_context


try:
    from accounts.models import Attendance as _Attendance, User as _User
    admin.site.unregister(_User)
    admin.site.unregister(_Attendance)
except Exception:
    pass

try:
    from patients.models import Patient as _Patient
    admin.site.unregister(_Patient)
except Exception:
    pass

try:
    from django.contrib.auth.models import Group as _Group
    admin.site.unregister(_Group)
except Exception:
    pass


class TenantCreateForm(forms.ModelForm):
    doctor_username = forms.CharField(
        max_length=150,
        required=True,
        label="اسم المستخدم للدكتور",
        help_text="سيتم إنشاؤه داخل قاعدة بيانات العيادة الجديدة.",
    )

    doctor_full_name = forms.CharField(
        max_length=150,
        required=True,
        label="الاسم الكامل للدكتور",
    )

    doctor_password = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput,
        label="كلمة مرور الدكتور",
    )

    class Meta:
        model = Tenant
        fields = (
            "clinic_name",
            "slug",
            "database_name",
            "database_host",
            "database_port",
            "database_user",
            "database_password",
            "status",
            "doctor_username",
            "doctor_full_name",
            "doctor_password",
        )

    def clean_database_name(self):
        db_name = self.cleaned_data.get("database_name")
        try:
            validate_database_name(db_name)
        except ValueError:
            raise forms.ValidationError(
                "اسم قاعدة البيانات غير صالح. يجب أن يبدأ بحرف "
                "ويحتوي على أحرف وأرقام وشرطات سفلية فقط (3-63 حرفاً)."
            )
        return db_name

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug.isascii() or not slug.replace("-", "").replace("_", "").isalnum():
            raise forms.ValidationError(
                "المعرف يجب أن يحتوي على أحرف إنجليزية وأرقام وشرطات فقط."
            )
        return slug


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "clinic_name",
        "slug",
        "database_name",
        "database_host",
        "database_port",
        "database_user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "database_host",
        "created_at",
    )

    search_fields = (
        "clinic_name",
        "slug",
        "database_name",
        "database_user",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "بيانات العيادة",
            {
                "fields": (
                    "clinic_name",
                    "slug",
                    "status",
                ),
            },
        ),
        (
            "إعدادات قاعدة البيانات",
            {
                "fields": (
                    "database_name",
                    "database_host",
                    "database_port",
                    "database_user",
                    "database_password",
                ),
            },
        ),
        (
            "تواريخ",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            "بيانات العيادة",
            {
                "fields": (
                    "clinic_name",
                    "slug",
                    "status",
                ),
            },
        ),
        (
            "إعدادات قاعدة البيانات",
            {
                "fields": (
                    "database_name",
                    "database_host",
                    "database_port",
                    "database_user",
                    "database_password",
                ),
            },
        ),
        (
            "الدكتور الأول",
            {
                "fields": (
                    "doctor_username",
                    "doctor_full_name",
                    "doctor_password",
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return TenantCreateForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        doctor_username = form.cleaned_data.get("doctor_username")
        doctor_full_name = form.cleaned_data.get("doctor_full_name")
        doctor_password = form.cleaned_data.get("doctor_password")

        created = False
        try:
            super().save_model(request, obj, form, change)
            created = True

            try:
                create_tenant_database(obj.database_name)
            except Exception as exc:
                raise RuntimeError(
                    f"فشل إنشاء قاعدة البيانات: {exc}"
                )

            try:
                configure_tenant_database(obj)
                connections["tenant"].ensure_connection()
            except Exception as exc:
                raise RuntimeError(
                    f"فشل الاتصال بقاعدة البيانات: {exc}"
                )

            try:
                migrate_tenant_database(obj)
            except Exception as exc:
                raise RuntimeError(
                    f"فشل تشغيل migrations: {exc}"
                )

            if doctor_username and doctor_full_name and doctor_password:
                set_current_tenant_db("tenant")
                try:
                    User = get_user_model()
                    User.objects.create_user(
                        username=doctor_username,
                        password=doctor_password,
                        full_name=doctor_full_name,
                        role=User.Role.DOCTOR,
                    )
                finally:
                    clear_current_tenant_db()

            messages.success(
                request,
                f"تم إنشاء العيادة \"{obj.clinic_name}\" بنجاح.\n"
                f"قاعدة البيانات: {obj.database_name}\n"
                f"الدكتور: {doctor_username}",
            )

        except Exception as exc:
            if created:
                try:
                    Tenant.objects.using("default").filter(id=obj.id).delete()
                except Exception:
                    pass
            try:
                connections["tenant"].close()
            except Exception:
                pass

            messages.error(
                request,
                f"فشل إنشاء العيادة: {exc}",
            )
            raise IntegrityError(str(exc)) from exc

        finally:
            try:
                connections["tenant"].close()
            except Exception:
                pass

    def response_add(self, request, obj, post_url_continue=None):
        try:
            return super().response_add(request, obj, post_url_continue)
        except IntegrityError:
            return self.response_post_save_add(request, obj)
