"""
Patient Views Module
Organized into logical submodules for better code organization
"""
from .secretary_views import (
    add_patient,
    secretary_patients,
    start_examination,
    complete_examination,
)

from .doctor_views import (
    doctor_patients,
    doctor_patient_file,
    create_patient_file,
    doctor_patient_detail,
    doctor_patient_add_note,
    doctor_patient_add_attachment,
    doctor_reports,
)

from .notification_views import (
    doctor_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    notification_count,
    delete_notification,
    clear_read_notifications,
)


__all__ = [
    # Secretary views
    'add_patient',
    'secretary_patients',
    'start_examination',
    'complete_examination',
    
    # Doctor views
    'doctor_patients',
    'doctor_patient_file',
    'create_patient_file',
    'doctor_patient_detail',
    'doctor_patient_add_note',
    'doctor_patient_add_attachment',
    'doctor_reports',
    
    # Notification views
    'doctor_notifications',
    'mark_notification_read',
    'mark_all_notifications_read',
    'notification_count',
    'delete_notification',
    'clear_read_notifications',
]
