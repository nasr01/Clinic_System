from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Attendance, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "full_name",
        "role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "full_name",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "معلومات العيادة",
            {
                "fields": (
                    "full_name",
                    "role",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "معلومات العيادة",
            {
                "fields": (
                    "full_name",
                    "role",
                )
            },
        ),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "check_in",
        "check_out",
        "work_duration",
    )

    list_filter = (
        "date",
        "employee",
    )

    search_fields = (
        "employee__username",
        "employee__full_name",
    )

    date_hierarchy = "date"

    ordering = ("-date", "-check_in")