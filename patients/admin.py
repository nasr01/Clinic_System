from django.contrib import admin

from .models import Patient, PatientNote, PatientAttachment, Notification


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "queue_number",
        "name",
        "age",
        "phone",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
    )

    ordering = (
        "queue_number",
    )


@admin.register(PatientNote)
class PatientNoteAdmin(admin.ModelAdmin):

    list_display = (
        "patient",
        "title",
        "doctor",
        "visit_date",
        "created_at",
    )

    list_filter = (
        "visit_date",
        "created_at",
    )

    search_fields = (
        "patient__name",
        "title",
        "content",
    )

    ordering = (
        "-visit_date",
        "-created_at",
    )


@admin.register(PatientAttachment)
class PatientAttachmentAdmin(admin.ModelAdmin):

    list_display = (
        "patient",
        "caption",
        "uploaded_by",
        "uploaded_at",
    )

    list_filter = (
        "uploaded_at",
    )

    search_fields = (
        "patient__name",
        "caption",
    )

    ordering = (
        "-uploaded_at",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "recipient",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "recipient__username",
        "title",
        "message",
    )

    ordering = (
        "-created_at",
    )