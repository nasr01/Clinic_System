"""
Secretary Views
Views for secretary-specific functionality: patient registration and queue management
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import secretary_required
from patients.forms import PatientForm
from patients.models import Patient
from patients.services import NotificationService, QueueService


@secretary_required
def add_patient(request):
    """
    Secretary view to add a new patient to today's queue
    """
    today = timezone.localdate()

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            # Use QueueService for thread-safe queue number generation
            patient_data = {
                'name': form.cleaned_data['name'],
                'age': form.cleaned_data['age'],
                'phone': form.cleaned_data['phone'],
                'visit_type': form.cleaned_data['visit_type'],
                'complaint': form.cleaned_data['complaint'],
                'status': Patient.Status.WAITING,
            }
            
            patient = QueueService.create_patient_with_queue(
                patient_data=patient_data,
                queue_date=today
            )

            # Notify all doctors using NotificationService
            NotificationService.notify_new_patient(patient)

            messages.success(
                request,
                f"تم تسجيل المريض {patient.name} بنجاح برقم الانتظار #{patient.queue_number}.",
            )

            return redirect("secretary_patients")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = PatientForm()

    # Get queue statistics
    queue_stats = QueueService.get_queue_stats(today)

    context = {
        "form": form,
        "today": today,
        "next_queue_number": queue_stats['next_queue_number'],
        "last_queue_number": queue_stats['last_queue_number'],
        "today_patients_count": queue_stats['total_patients'],
    }

    return render(request, "patients/add_patient.html", context)


@secretary_required
def secretary_patients(request):
    """
    Secretary view to see all patients in today's queue
    """
    today = timezone.localdate()

    patients = Patient.objects.filter(queue_date=today).order_by("queue_number")

    # Get queue statistics
    queue_stats = QueueService.get_queue_stats(today)

    context = {
        "patients": patients,
        "today": today,
        "total_patients": queue_stats['total_patients'],
        "waiting_patients": queue_stats['waiting_patients'],
        "in_examination_patients": queue_stats['in_examination_patients'],
        "completed_patients": queue_stats['completed_patients'],
    }

    return render(request, "patients/secretary_patients.html", context)


@secretary_required
def start_examination(request, patient_id):
    """
    Secretary view to mark a patient as 'in examination'
    """
    if request.method == "POST":
        patient = Patient.objects.get(
            id=patient_id,
            queue_date=timezone.localdate(),
        )

        if patient.status == Patient.Status.WAITING:
            patient.status = Patient.Status.IN_EXAMINATION
            patient.examination_started_at = timezone.now()

            patient.save(update_fields=["status", "examination_started_at"])

            # Notify doctors using NotificationService
            NotificationService.notify_examination_started(patient)

            messages.success(request, f"تم بدء الكشف للمريض {patient.name}.")

    return redirect("secretary_patients")


@secretary_required
def complete_examination(request, patient_id):
    """
    Secretary view to mark a patient as 'completed'
    """
    if request.method == "POST":
        patient = Patient.objects.get(
            id=patient_id,
            queue_date=timezone.localdate(),
        )

        if patient.status == Patient.Status.IN_EXAMINATION:
            patient.status = Patient.Status.COMPLETED
            patient.completed_at = timezone.now()

            patient.save(update_fields=["status", "completed_at"])

            # Notify doctors using NotificationService
            NotificationService.notify_examination_completed(patient)

            messages.success(request, f"تم إنهاء الكشف للمريض {patient.name} بنجاح.")

    return redirect("secretary_patients")
