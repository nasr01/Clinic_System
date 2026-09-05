from django.urls import path

from .views import (
    add_patient,
    complete_examination,
    create_patient_file,
    doctor_notifications,
    doctor_patient_add_attachment,
    doctor_patient_add_note,
    doctor_patient_detail,
    doctor_patient_file,
    doctor_patients,
    doctor_reports,
    mark_all_notifications_read,
    mark_notification_read,
    notification_count,
    secretary_patients,
    start_examination,
)


urlpatterns = [
    # Secretary
    path(
        "patients/",
        secretary_patients,
        name="secretary_patients",
    ),

    path(
        "patients/add/",
        add_patient,
        name="add_patient",
    ),

    path(
        "patients/<int:patient_id>/start/",
        start_examination,
        name="start_examination",
    ),

    path(
        "patients/<int:patient_id>/complete/",
        complete_examination,
        name="complete_examination",
    ),

    # Doctor
    path(
        "doctor/patients/",
        doctor_patients,
        name="doctor_patients",
    ),

    path(
        "doctor/patients/file/",
        doctor_patient_file,
        name="doctor_patient_file",
    ),

    path(
        "doctor/reports/",
        doctor_reports,
        name="doctor_reports",
    ),

    path(
        "doctor/patients/<int:patient_id>/",
        doctor_patient_detail,
        name="doctor_patient_detail",
    ),

    path(
        "doctor/patients/<int:patient_id>/add-note/",
        doctor_patient_add_note,
        name="doctor_patient_add_note",
    ),

    path(
        "doctor/patients/<int:patient_id>/add-attachment/",
        doctor_patient_add_attachment,
        name="doctor_patient_add_attachment",
    ),

    path(
        "doctor/patients/<int:patient_id>/create-file/",
        create_patient_file,
        name="create_patient_file",
    ),

    path(
        "doctor/notifications/",
        doctor_notifications,
        name="doctor_notifications",
    ),

    path(
        "doctor/notifications/<int:notification_id>/read/",
        mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "doctor/notifications/read-all/",
        mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),

    path(
        "doctor/notifications/count/",
        notification_count,
        name="notification_count",
    ),
]