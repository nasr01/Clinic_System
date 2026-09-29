"""
Doctor Views
Views for doctor-specific functionality: patient files, notes, attachments, and reports
"""
from datetime import datetime

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from accounts.decorators import doctor_required
from patients.forms import (
    DoctorPatientFileForm,
    PatientAttachmentForm,
    PatientNoteForm,
)
from patients.models import Patient
from patients.services import QueueService


@doctor_required
def doctor_patients(request):
    """
    Doctor view to see all patients in today's queue
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

    return render(request, "patients/doctor_patients.html", context)


@doctor_required
def doctor_patient_file(request):
    """
    Doctor view to browse patient files and create new patient files
    """
    query = request.GET.get("q", "").strip()
    patients_qs = Patient.objects.filter(has_file=True).order_by("-file_created_at", "-id")

    show_create = request.GET.get("create", "0") == "1"
    create_form = None

    if request.method == "POST" and "create_patient" in request.POST:
        create_form = DoctorPatientFileForm(request.POST)
        if create_form.is_valid():
            patient = create_form.save()
            messages.success(
                request,
                f"تم إنشاء ملف المريض {patient.name} بنجاح برقم #{patient.id}.",
            )
            return redirect("doctor_patient_detail", patient_id=patient.id)
        else:
            for field, errors in create_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    if query:
        if query.isdigit():
            patients_qs = patients_qs.filter(
                Q(id=int(query)) | Q(name__icontains=query)
            )
        else:
            patients_qs = patients_qs.filter(name__icontains=query)

    if create_form is None:
        create_form = DoctorPatientFileForm()

    no_file_count = Patient.objects.filter(has_file=False).count()

    context = {
        "patients": patients_qs,
        "total_patients": patients_qs.count(),
        "all_patients_count": Patient.objects.filter(has_file=True).count(),
        "no_file_count": no_file_count,
        "query": query,
        "show_create": show_create,
        "create_form": create_form,
    }

    return render(request, "patients/doctor_patient_file.html", context)


@doctor_required
def create_patient_file(request, patient_id):
    """
    Doctor view to create a file for an existing patient who doesn't have one
    """
    if request.method != "POST":
        messages.info(request, "يرجى استخدام زر إنشاء الملف.")
        return redirect("doctor_patient_detail", patient_id=patient_id)

    patient = get_object_or_404(Patient, id=patient_id)

    if not patient.has_file:
        patient.has_file = True
        patient.file_created_at = timezone.now()
        patient.save(update_fields=["has_file", "file_created_at"])
        messages.success(request, f"تم إنشاء ملف المريض {patient.name} بنجاح.")
    else:
        messages.info(request, "للمريض ملف بالفعل.")

    return redirect("doctor_patient_detail", patient_id=patient.id)


@doctor_required
def doctor_patient_detail(request, patient_id):
    """
    Doctor view to see detailed patient information, notes, and attachments
    """
    patient = get_object_or_404(Patient, id=patient_id)
    notes = patient.notes.all().select_related("doctor")
    attachments = patient.attachments.all().select_related("uploaded_by")

    note_form = PatientNoteForm(initial={"visit_date": timezone.localdate()})
    attachment_form = PatientAttachmentForm()

    context = {
        "patient": patient,
        "notes": notes,
        "attachments": attachments,
        "notes_count": notes.count(),
        "attachments_count": attachments.count(),
        "note_form": note_form,
        "attachment_form": attachment_form,
    }

    return render(request, "patients/doctor_patient_detail.html", context)


@doctor_required
def doctor_patient_add_note(request, patient_id):
    """
    Doctor view to add a note to a patient's file
    """
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        form = PatientNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.patient = patient
            note.doctor = request.user
            note.save()
            messages.success(
                request,
                f"تمت إضافة الملاحظة بنجاح لمريض {patient.name}.",
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return redirect("doctor_patient_detail", patient_id=patient.id)


@doctor_required
def doctor_patient_add_attachment(request, patient_id):
    """
    Doctor view to add an attachment to a patient's file
    """
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        form = PatientAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.patient = patient
            attachment.uploaded_by = request.user
            attachment.save()
            messages.success(
                request,
                f"تم رفع الملف {attachment.caption or attachment.filename} بنجاح.",
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return redirect("doctor_patient_detail", patient_id=patient.id)


@doctor_required
def doctor_reports(request):
    """
    Doctor view to generate reports for completed visits within a date range
    """
    today = timezone.localdate()
    first_day_of_month = today.replace(day=1)

    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            from_date = first_day_of_month
    else:
        from_date = first_day_of_month

    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            to_date = today
    else:
        to_date = today

    completed_visits = Patient.objects.filter(
        status=Patient.Status.COMPLETED,
        queue_date__gte=from_date,
        queue_date__lte=to_date,
    ).order_by('-queue_date', '-queue_number')

    total_visits = completed_visits.count()
    total_examinations = completed_visits.filter(
        visit_type=Patient.VisitType.EXAMINATION
    ).count()
    total_consultations = completed_visits.filter(
        visit_type=Patient.VisitType.CONSULTATION
    ).count()

    context = {
        'from_date': from_date,
        'to_date': to_date,
        'completed_visits': completed_visits,
        'total_visits': total_visits,
        'total_examinations': total_examinations,
        'total_consultations': total_consultations,
    }

    return render(request, 'patients/doctor_reports.html', context)
