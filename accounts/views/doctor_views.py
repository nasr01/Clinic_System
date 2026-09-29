"""
Doctor-Specific Account Views
Dashboard and employee management for doctors
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import doctor_required
from accounts.models import User
from patients.models import Patient
from patients.services import QueueService


@doctor_required
def doctor_dashboard(request):
    """
    Doctor dashboard showing today's patient queue summary
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

    return render(request, "doctor/dashboard.html", context)


@doctor_required
def doctor_employees(request):
    """
    Doctor view to manage secretary employees
    """
    employees = (
        User.objects
        .filter(role=User.Role.SECRETARY)
        .order_by("-date_joined")
    )

    form_errors = {}
    form_data = {}

    if request.method == "POST" and "create_employee" in request.POST:
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        form_data = {
            "full_name": full_name,
            "username": username,
        }

        if not full_name:
            form_errors["full_name"] = "يرجى إدخال اسم الموظف."

        if not username:
            form_errors["username"] = "يرجى إدخال اسم المستخدم."
        elif User.objects.filter(username=username).exists():
            form_errors["username"] = "اسم المستخدم موجود بالفعل."

        if not password:
            form_errors["password"] = "يرجى إدخال كلمة المرور."
        elif len(password) < 6:
            form_errors["password"] = "كلمة المرور يجب أن تكون 6 أحرف على الأقل."
        elif password != password_confirm:
            form_errors["password"] = "كلمات المرور غير متطابقة."

        if not form_errors:
            user = User.objects.create_user(
                username=username,
                password=password,
                full_name=full_name,
                role=User.Role.SECRETARY,
            )

            messages.success(
                request,
                f"تم إنشاء حساب السكرتير {user.full_name} بنجاح.",
            )

            return redirect("doctor_employees")

    context = {
        "employees": employees,
        "form_errors": form_errors,
        "form_data": form_data,
    }

    return render(request, "doctor/employees.html", context)
