from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import PatientForm
from .models import Patient


def redirect_by_role(user):
    if user.role == "doctor":
        return redirect("doctor_dashboard")

    if user.role == "secretary":
        return redirect("secretary_dashboard")

    return redirect("login")


@login_required
def add_patient(request):
    if request.user.role != "secretary":
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

            messages.success(
                request,
                f"تم تسجيل المريض {patient.name} بنجاح برقم الانتظار #{patient.queue_number}.",
            )

            return redirect("secretary_patients")

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
    if request.user.role != "secretary":
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
    if request.user.role != "doctor":
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
    if request.user.role != "doctor":
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
            messages.success(
                request,
                f"تم بدء الكشف للمريض {patient.name}.",
            )

    return redirect("doctor_patients")


@login_required
def complete_examination(request, patient_id):
    if request.user.role != "doctor":
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
            messages.success(
                request,
                f"تم إنهاء الكشف للمريض {patient.name} بنجاح.",
            )

    return redirect("doctor_patients")
