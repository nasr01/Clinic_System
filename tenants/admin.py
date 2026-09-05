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
    drop_tenant_database,
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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        
        # After creation, database connection fields become immutable
        # to prevent pointing to non-existent databases
        if obj is not None:
            readonly.extend([
                'database_name',
                'database_host',
                'database_port',
                'database_user',
            ])
        
        return tuple(readonly)

    def delete_model(self, request, obj):
        """
        Override delete to prevent accidental PostgreSQL database destruction.
        
        Only the Tenant record is deleted from the control database.
        The actual PostgreSQL database is NOT dropped to prevent data loss.
        
        Admin must manually drop the database if permanent deletion is intended.
        """
        database_name = obj.database_name
        
        # Delete only the Tenant record
        super().delete_model(request, obj)
        
        messages.warning(
            request,
            f"تم حذف سجل العيادة \"{obj.clinic_name}\" من النظام.\n"
            f"ملاحظة مهمة: قاعدة البيانات \"{database_name}\" لم يتم حذفها.\n"
            f"إذا كنت تريد حذفها نهائياً، يجب حذفها يدوياً من PostgreSQL."
        )

    def delete_queryset(self, request, queryset):
        """
        Override bulk delete to prevent accidental PostgreSQL database destruction.
        """
        database_names = list(queryset.values_list('database_name', flat=True))
        count = queryset.count()
        
        # Delete only the Tenant records
        super().delete_queryset(request, queryset)
        
        messages.warning(
            request,
            f"تم حذف {count} سجل عيادة من النظام.\n"
            f"ملاحظة مهمة: قواعد البيانات التالية لم يتم حذفها:\n"
            f"{', '.join(database_names)}\n"
            f"إذا كنت تريد حذفها نهائياً، يجب حذفها يدوياً من PostgreSQL."
        )

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        doctor_username = form.cleaned_data.get("doctor_username")
        doctor_full_name = form.cleaned_data.get("doctor_full_name")
        doctor_password = form.cleaned_data.get("doctor_password")

        tenant_created = False
        database_created = False
        
        try:
            # Step 1: Save Tenant record
            super().save_model(request, obj, form, change)
            tenant_created = True

            # Step 2: Create PostgreSQL database
            try:
                database_created = create_tenant_database(obj.database_name)
            except Exception as exc:
                raise RuntimeError(
                    f"فشل إنشاء قاعدة البيانات: {exc}"
                )

            # Step 3: Configure tenant database connection
            try:
                configure_tenant_database(obj)
                connections["tenant"].ensure_connection()
            except Exception as exc:
                raise RuntimeError(
                    f"فشل الاتصال بقاعدة البيانات: {exc}"
                )

            # Step 4: Run migrations
            try:
                migrate_tenant_database(obj)
            except Exception as exc:
                raise RuntimeError(
                    f"فشل تشغيل migrations: {exc}"
                )

            # Step 5: Create first doctor
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
            # Cleanup on failure
            
            # Close any open tenant connections
            try:
                connections["tenant"].close()
            except Exception:
                pass
            
            # Drop the database ONLY if we created it in this operation
            if database_created:
                try:
                    drop_tenant_database(obj.database_name)
                except Exception as drop_exc:
                    # Log but don't fail - admin needs to manually clean up
                    messages.warning(
                        request,
                        f"تحذير: فشل حذف قاعدة البيانات {obj.database_name} تلقائياً. "
                        f"قد تحتاج إلى حذفها يدوياً. خطأ: {drop_exc}"
                    )
            
            # Remove Tenant record if it was created
            if tenant_created:
                try:
                    Tenant.objects.using("default").filter(id=obj.id).delete()
                except Exception:
                    pass

            messages.error(
                request,
                f"فشل إنشاء العيادة: {exc}",
            )
            raise IntegrityError(str(exc)) from exc

        finally:
            # Always close tenant connection
            try:
                connections["tenant"].close()
            except Exception:
                pass

    def response_add(self, request, obj, post_url_continue=None):
        try:
            return super().response_add(request, obj, post_url_continue)
        except IntegrityError:
            return self.response_post_save_add(request, obj)
