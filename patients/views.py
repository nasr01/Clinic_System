from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Count, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from .forms import (
    DoctorPatientFileForm,
    PatientAttachmentForm,
    PatientForm,
    PatientNoteForm,
)
from .models import Patient, Notification


def redirect_by_role(user):
    user_role = getattr(user, 'role', None)

    if user_role == "doctor":
        return redirect("doctor_dashboard")

    if user_role == "secretary":
        return redirect("secretary_dashboard")

    return redirect("login")


def create_notification(recipient, notification_type, title, message, patient=None):
    """
    Helper function to create notifications for doctors
    """
    from accounts.models import User
    
    # If recipient is "all_doctors", send to all doctors
    if recipient == "all_doctors":
        doctors = User.objects.filter(role=User.Role.DOCTOR)
        for doctor in doctors:
            Notification.objects.create(
                recipient=doctor,
                notification_type=notification_type,
                title=title,
                message=message,
                patient=patient,
            )
    else:
        Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            patient=patient,
        )


@login_required
def add_patient(request):
    if getattr(request.user, 'role', None) != "secretary":
        return redirect_by_role(request.user)

    today = timezone.localdate()

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            patient = form.save(commit=False)

            last_queue = (
                Patient.objects.filter(queue_date=today)
                .aggregate(Max("queue_number"))["queue_number__max"]
            )

            patient.queue_date = today
            patient.queue_number = (last_queue or 0) + 1
            patient.status = Patient.Status.WAITING

            patient.save()

            # Create notification for all doctors
            create_notification(
                recipient="all_doctors",
                notification_type=Notification.Type.NEW_PATIENT,
                title=f"مريض جديد: {patient.name}",
                message=f"تم تسجيل مريض جديد: {patient.name} ({patient.age} سنة) - رقم الانتظار #{patient.queue_number}",
                patient=patient,
            )

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

    last_queue = (
        Patient.objects.filter(queue_date=today)
        .aggregate(Max("queue_number"))["queue_number__max"]
    )
    today_count = Patient.objects.filter(queue_date=today).count()

    context = {
        "form": form,
        "today": today,
        "next_queue_number": (last_queue or 0) + 1,
        "last_queue_number": last_queue or 0,
        "today_patients_count": today_count,
    }

    return render(
        request,
        "patients/add_patient.html",
        context,
    )


@login_required
def secretary_patients(request):
    if getattr(request.user, 'role', None) != "secretary":
        return redirect_by_role(request.user)

    today = timezone.localdate()

    patients = (
        Patient.objects.filter(queue_date=today).order_by("queue_number")
    )

    context = {
        "patients": patients,
        "today": today,
        "total_patients": patients.count(),
        "waiting_patients": patients.filter(
            status=Patient.Status.WAITING
        ).count(),
        "in_examination_patients": patients.filter(
            status=Patient.Status.IN_EXAMINATION
        ).count(),
        "completed_patients": patients.filter(
            status=Patient.Status.COMPLETED
        ).count(),
    }

    return render(
        request,
        "patients/secretary_patients.html",
        context,
    )


@login_required
def doctor_patients(request):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

    today = timezone.localdate()

    patients = (
        Patient.objects.filter(queue_date=today).order_by("queue_number")
    )

    context = {
        "patients": patients,
        "today": today,
        "total_patients": patients.count(),
        "waiting_patients": patients.filter(
            status=Patient.Status.WAITING
        ).count(),
        "in_examination_patients": patients.filter(
            status=Patient.Status.IN_EXAMINATION
        ).count(),
        "completed_patients": patients.filter(
            status=Patient.Status.COMPLETED
        ).count(),
    }

    return render(
        request,
        "patients/doctor_patients.html",
        context,
    )


@login_required
def start_examination(request, patient_id):
    if getattr(request.user, 'role', None) != "secretary":
        messages.error(request, "غير مسموح لك ببدء الكشف.")
        return redirect_by_role(request.user)

    if request.method == "POST":
        patient = Patient.objects.get(
            id=patient_id,
            queue_date=timezone.localdate(),
        )

        if patient.status == Patient.Status.WAITING:
            patient.status = Patient.Status.IN_EXAMINATION
            patient.examination_started_at = timezone.now()

            patient.save(
                update_fields=[
                    "status",
                    "examination_started_at",
                ]
            )

            # Create notification for all doctors
            create_notification(
                recipient="all_doctors",
                notification_type=Notification.Type.PATIENT_STARTED,
                title=f"بدء الكشف: {patient.name}",
                message=f"تم بدء الكشف للمريض {patient.name} - رقم الانتظار #{patient.queue_number}",
                patient=patient,
            )

            messages.success(
                request,
                f"تم بدء الكشف للمريض {patient.name}.",
            )

    return redirect("secretary_patients")


@login_required
def complete_examination(request, patient_id):
    if getattr(request.user, 'role', None) != "secretary":
        messages.error(request, "غير مسموح لك بإنهاء الكشف.")
        return redirect_by_role(request.user)

    if request.method == "POST":
        patient = Patient.objects.get(
            id=patient_id,
            queue_date=timezone.localdate(),
        )

        if patient.status == Patient.Status.IN_EXAMINATION:
            patient.status = Patient.Status.COMPLETED
            patient.completed_at = timezone.now()

            patient.save(
                update_fields=[
                    "status",
                    "completed_at",
                ]
            )

            # Create notification for all doctors
            create_notification(
                recipient="all_doctors",
                notification_type=Notification.Type.PATIENT_COMPLETED,
                title=f"إنهاء الكشف: {patient.name}",
                message=f"تم إنهاء الكشف للمريض {patient.name} بنجاح",
                patient=patient,
            )

            messages.success(
                request,
                f"تم إنهاء الكشف للمريض {patient.name} بنجاح.",
            )

    return redirect("secretary_patients")


@login_required
def doctor_patient_file(request):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

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

    return render(
        request,
        "patients/doctor_patient_file.html",
        context,
    )


@login_required
def create_patient_file(request, patient_id):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

    if request.method != "POST":
        messages.info(request, "يرجى استخدام زر إنشاء الملف.")
        return redirect("doctor_patient_detail", patient_id=patient_id)

    patient = get_object_or_404(Patient, id=patient_id)

    if not patient.has_file:
        patient.has_file = True
        patient.file_created_at = timezone.now()
        patient.save(update_fields=["has_file", "file_created_at"])
        messages.success(
            request,
            f"تم إنشاء ملف المريض {patient.name} بنجاح.",
        )
    else:
        messages.info(request, "للمريض ملف بالفعل.")

    return redirect("doctor_patient_detail", patient_id=patient.id)


@login_required
def doctor_patient_detail(request, patient_id):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

    patient = get_object_or_404(Patient, id=patient_id)
    notes = patient.notes.all().select_related("doctor")
    attachments = patient.attachments.all().select_related("uploaded_by")

    note_form = PatientNoteForm(
        initial={"visit_date": timezone.localdate()}
    )
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

    return render(
        request,
        "patients/doctor_patient_detail.html",
        context,
    )


@login_required
def doctor_patient_add_note(request, patient_id):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

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


@login_required
def doctor_patient_add_attachment(request, patient_id):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

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


@login_required
def doctor_reports(request):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

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

    return render(
        request,
        'patients/doctor_reports.html',
        context,
    )


@login_required
def doctor_notifications(request):
    if getattr(request.user, 'role', None) != "doctor":
        return redirect_by_role(request.user)

    # Let the router handle database selection automatically
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")
    unread_count = notifications.filter(is_read=False).count()

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
    }

    return render(
        request,
        "patients/doctor_notifications.html",
        context,
    )


@login_required
def mark_notification_read(request, notification_id):
    if getattr(request.user, 'role', None) != "doctor":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notification not found"}, status=404)


@login_required
def mark_all_notifications_read(request):
    if getattr(request.user, 'role', None) != "doctor":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})


@login_required
def notification_count(request):
    if getattr(request.user, 'role', None) != "doctor":
        return JsonResponse({"count": 0})

    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({"count": count})
