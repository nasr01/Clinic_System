"""
Queue Service
Service for managing patient queue numbers with race condition protection
"""
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from patients.models import Patient


class QueueService:
    """
    Service class for handling patient queue number generation
    Uses database-level advisory locks to prevent race conditions
    """

    @staticmethod
    def _get_lock_id(queue_date):
        """
        Generate a unique lock ID for a given queue date.
        Uses date as integer (YYYYMMDD) for PostgreSQL advisory lock.
        """
        return int(queue_date.strftime('%Y%m%d'))

    @staticmethod
    @transaction.atomic
    def create_patient_with_queue(patient_data, queue_date=None):
        """
        Create a patient with automatic queue number assignment.
        Uses PostgreSQL advisory locks to ensure thread-safe queue number generation,
        even when no patients exist for the date.
        
        Args:
            patient_data: Dictionary containing patient fields (name, age, phone, etc.)
            queue_date: Date for the queue (defaults to today)
        
        Returns:
            Patient: Created patient object
        """
        if queue_date is None:
            queue_date = timezone.localdate()
        
        lock_id = QueueService._get_lock_id(queue_date)
        
        # Acquire advisory lock for this date's queue
        # This blocks other transactions trying to get the same lock
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
        
        # Now we have exclusive access to this date's queue
        # Get the next queue number safely
        last_queue = (
            Patient.objects
            .filter(queue_date=queue_date)
            .aggregate(Max('queue_number'))['queue_number__max']
        )
        
        next_queue = (last_queue or 0) + 1
        
        # Create the patient
        patient = Patient.objects.create(
            queue_date=queue_date,
            queue_number=next_queue,
            **patient_data
        )
        
        # Lock is automatically released at transaction end
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
        
        last_queue = patients.aggregate(Max('queue_number'))['queue_number__max'] or 0
        
        return {
            'total_patients': patients.count(),
            'waiting_patients': patients.filter(status=Patient.Status.WAITING).count(),
            'in_examination_patients': patients.filter(status=Patient.Status.IN_EXAMINATION).count(),
            'completed_patients': patients.filter(status=Patient.Status.COMPLETED).count(),
            'last_queue_number': last_queue,
            'next_queue_number': last_queue + 1,
        }
