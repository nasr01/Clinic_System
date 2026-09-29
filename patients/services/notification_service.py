"""
Notification Service
Centralized service for creating and managing notifications
"""
from patients.models import Notification


class NotificationService:
    """
    Service class for handling notification creation and management
    """

    @staticmethod
    def create_notification(recipient, notification_type, title, message, patient=None):
        """
        Create a notification for a single recipient
        
        Args:
            recipient: User object to receive the notification
            notification_type: Type of notification (from Notification.Type)
            title: Notification title
            message: Notification message
            patient: Optional Patient object related to this notification
        
        Returns:
            Notification object
        """
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            patient=patient,
        )

    @staticmethod
    def notify_all_doctors(notification_type, title, message, patient=None):
        """
        Create notifications for all doctors in the system
        
        Args:
            notification_type: Type of notification (from Notification.Type)
            title: Notification title
            message: Notification message
            patient: Optional Patient object related to this notification
        
        Returns:
            List of created Notification objects
        """
        from accounts.models import User
        
        doctors = User.objects.filter(role=User.Role.DOCTOR)
        notifications = []
        
        for doctor in doctors:
            notification = NotificationService.create_notification(
                recipient=doctor,
                notification_type=notification_type,
                title=title,
                message=message,
                patient=patient,
            )
            notifications.append(notification)
        
        return notifications

    @staticmethod
    def notify_new_patient(patient):
        """
        Notify all doctors about a new patient registration
        
        Args:
            patient: Patient object
        """
        return NotificationService.notify_all_doctors(
            notification_type=Notification.Type.NEW_PATIENT,
            title=f"مريض جديد: {patient.name}",
            message=f"تم تسجيل مريض جديد: {patient.name} ({patient.age} سنة) - رقم الانتظار #{patient.queue_number}",
            patient=patient,
        )

    @staticmethod
    def notify_examination_started(patient):
        """
        Notify all doctors that examination has started for a patient
        
        Args:
            patient: Patient object
        """
        return NotificationService.notify_all_doctors(
            notification_type=Notification.Type.PATIENT_STARTED,
            title=f"بدء الكشف: {patient.name}",
            message=f"تم بدء الكشف للمريض {patient.name} - رقم الانتظار #{patient.queue_number}",
            patient=patient,
        )

    @staticmethod
    def notify_examination_completed(patient):
        """
        Notify all doctors that examination has been completed for a patient
        
        Args:
            patient: Patient object
        """
        return NotificationService.notify_all_doctors(
            notification_type=Notification.Type.PATIENT_COMPLETED,
            title=f"إنهاء الكشف: {patient.name}",
            message=f"تم إنهاء الكشف للمريض {patient.name} بنجاح",
            patient=patient,
        )

    @staticmethod
    def notify_attendance_check_in(employee, time_str):
        """
        Notify all doctors about employee check-in
        
        Args:
            employee: User object (secretary)
            time_str: Formatted check-in time string
        """
        user_name = employee.get_full_name() or employee.username
        
        return NotificationService.notify_all_doctors(
            notification_type=Notification.Type.ATTENDANCE,
            title=f"تسجيل حضور: {user_name}",
            message=f"قام {user_name} بتسجيل الحضور في {time_str}",
        )

    @staticmethod
    def notify_attendance_check_out(employee, time_str, work_duration):
        """
        Notify all doctors about employee check-out
        
        Args:
            employee: User object (secretary)
            time_str: Formatted check-out time string
            work_duration: Work duration string
        """
        user_name = employee.get_full_name() or employee.username
        
        return NotificationService.notify_all_doctors(
            notification_type=Notification.Type.ATTENDANCE,
            title=f"تسجيل انصراف: {user_name}",
            message=f"قام {user_name} بتسجيل الانصراف في {time_str} - مدة العمل: {work_duration}",
        )
