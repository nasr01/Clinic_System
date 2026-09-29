"""
Secretary-Specific Account Views
Dashboard and attendance management for secretaries
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import secretary_required
from accounts.models import Attendance
from patients.models import Patient
from patients.services import NotificationService, QueueService


@login_required
@secretary_required
def secretary_dashboard(request):
    """
    Secretary dashboard showing today's patient queue summary
    """
    today = timezone.localdate()

    patients = Patient.objects.filter(queue_date=today)
    today_patients = patients.order_by("queue_number")

    # Get queue statistics
    queue_stats = QueueService.get_queue_stats(today)

    context = {
        "user": request.user,
        "today": today,
        "total_patients": queue_stats['total_patients'],
        "waiting_patients": queue_stats['waiting_patients'],
        "in_examination_patients": queue_stats['in_examination_patients'],
        "completed_patients": queue_stats['completed_patients'],
        "today_patients": today_patients,
    }

    return render(request, "secretary/dashboard.html", context)


@login_required
@secretary_required
def secretary_attendance(request):
    """
    Secretary view to manage check-in and check-out
    """
    today = timezone.localdate()
    now = timezone.now()

    # Get user's display name
    user_name = request.user.get_full_name() or request.user.username

    try:
        attendance = Attendance.objects.get(
            employee=request.user,
            date=today,
        )
    except Attendance.DoesNotExist:
        attendance = None

    if request.method == "POST":
        action = request.POST.get("action")

        # Check In
        if action == "check_in":
            if attendance is None:
                attendance = Attendance.objects.create(
                    employee=request.user,
                    date=today,
                    check_in=now,
                )

                # Notify doctors using NotificationService
                NotificationService.notify_attendance_check_in(
                    employee=request.user,
                    time_str=now.strftime('%H:%M')
                )

                messages.success(
                    request,
                    "تم تسجيل الحضور بنجاح. أتمنى لك يومًا سعيدًا!",
                )

            elif attendance.check_in is None:
                attendance.check_in = now
                attendance.save(update_fields=["check_in"])
                messages.success(request, "تم تسجيل الحضور بنجاح.")

        # Check Out
        elif action == "check_out":
            if (
                attendance
                and attendance.check_in
                and attendance.check_out is None
            ):
                attendance.check_out = now
                attendance.save(update_fields=["check_out"])

                # Notify doctors using NotificationService
                NotificationService.notify_attendance_check_out(
                    employee=request.user,
                    time_str=now.strftime('%H:%M'),
                    work_duration=attendance.work_duration
                )

                messages.success(
                    request,
                    f"تم تسجيل الانصراف بنجاح. مدة العمل: {attendance.work_duration}",
                )

        return redirect("secretary_attendance")

    recent_attendances = (
        Attendance.objects
        .filter(employee=request.user)
        .exclude(date=today)
        .order_by("-date")[:10]
    )

    context = {
        "today": today,
        "attendance": attendance,
        "recent_attendances": recent_attendances,
    }

    return render(request, "secretary/attendance.html", context)
