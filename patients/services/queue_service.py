"""
Queue Service
Service for managing patient queue numbers with race condition protection
"""
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from patients.models import Patient


class QueueService:
    """
    Service class for handling patient queue number generation
    Uses database-level locking to prevent race conditions
    """

    @staticmethod
    @transaction.atomic
    def get_next_queue_number(queue_date=None):
        """
        Get the next available queue number for a given date.
        Uses select_for_update to prevent race conditions.
        
        Args:
            queue_date: Date for the queue (defaults to today)
        
        Returns:
            int: Next queue number
        """
        if queue_date is None:
            queue_date = timezone.localdate()
        
        # Lock the rows to prevent race conditions
        # Use select_for_update to ensure atomic read and increment
        last_patient = (
            Patient.objects
            .filter(queue_date=queue_date)
            .select_for_update()
            .order_by('-queue_number')
            .first()
        )
        
        if last_patient:
            return last_patient.queue_number + 1
        else:
            return 1

    @staticmethod
    @transaction.atomic
    def create_patient_with_queue(patient_data, queue_date=None):
        """
        Create a patient with automatic queue number assignment.
        This method ensures thread-safe queue number generation.
        
        Args:
            patient_data: Dictionary containing patient fields (name, age, phone, etc.)
            queue_date: Date for the queue (defaults to today)
        
        Returns:
            Patient: Created patient object
        """
        if queue_date is None:
            queue_date = timezone.localdate()
        
        # Get next queue number atomically
        next_queue = QueueService.get_next_queue_number(queue_date)
        
        # Create the patient
        patient = Patient.objects.create(
            queue_date=queue_date,
            queue_number=next_queue,
            **patient_data
        )
        
        return patient

    @staticmethod
    def get_queue_stats(queue_date=None):
        """
        Get statistics about the queue for a given date.
        
        Args:
            queue_date: Date for the queue (defaults to today)
        
        Returns:
            dict: Dictionary containing queue statistics
        """
        if queue_date is None:
            queue_date = timezone.localdate()
        
        patients = Patient.objects.filter(queue_date=queue_date)
        
        return {
            'total_patients': patients.count(),
            'waiting_patients': patients.filter(status=Patient.Status.WAITING).count(),
            'in_examination_patients': patients.filter(status=Patient.Status.IN_EXAMINATION).count(),
            'completed_patients': patients.filter(status=Patient.Status.COMPLETED).count(),
            'last_queue_number': patients.aggregate(Max('queue_number'))['queue_number__max'] or 0,
            'next_queue_number': QueueService._get_next_queue_number_no_lock(queue_date),
        }

    @staticmethod
    def _get_next_queue_number_no_lock(queue_date):
        """
        Get next queue number without locking (for read-only operations like display).
        
        Args:
            queue_date: Date for the queue
        
        Returns:
            int: Next queue number (estimated)
        """
        last_queue = (
            Patient.objects
            .filter(queue_date=queue_date)
            .aggregate(Max('queue_number'))['queue_number__max']
        )
        
        return (last_queue or 0) + 1
