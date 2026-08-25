from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Attendance, User

from tenants.manager import configure_tenant_database
from tenants.models import Tenant
from tenants.routers import (
    set_current_tenant_db,
    clear_current_tenant_db,
)


def redirect_by_role(user):
    if user.role == User.Role.DOCTOR:
        return redirect("doctor_dashboard")

    if user.role == User.Role.SECRETARY:
        return redirect("secretary_dashboard")

    return redirect("login")


def login_view(request):

    if request.method == "POST":

        clinic_slug = request.POST.get(
            "clinic_slug",
            "",
        ).strip()

        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        context = {
            "clinic_slug": clinic_slug,
            "username": username,
        }

        # =========================
        # Validation
        # =========================

        if not clinic_slug:
            context["error"] = "يرجى إدخال معرف العيادة."
            return render(
                request,
                "accounts/login.html",
                context,
            )

        if not username or not password:
            context["error"] = (
                "يرجى إدخال اسم المستخدم وكلمة المرور."
            )

            return render(
                request,
                "accounts/login.html",
                context,
            )

        # =========================
        # Get Tenant
        # =========================

        try:
            tenant = (
                Tenant.objects
                .using("default")
                .get(
                    slug=clinic_slug,
                    status=Tenant.Status.ACTIVE,
                )
            )

        except Tenant.DoesNotExist:

            context["error"] = (
                "العيادة غير موجودة أو موقوفة."
            )

            return render(
                request,
                "accounts/login.html",
                context,
            )

        # =========================
        # Configure Tenant DB
        # =========================

        configure_tenant_database(tenant)

        set_current_tenant_db("tenant")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        # =========================
        # Invalid Login
        # =========================

        if user is None:

            clear_current_tenant_db()

            context["error"] = (
                "اسم المستخدم أو كلمة المرور غير صحيحة."
            )

            return render(
                request,
                "accounts/login.html",
                context,
            )

        # =========================
        # Save Tenant in Session
        # =========================

        request.session["tenant_id"] = tenant.id
        request.session["tenant_slug"] = tenant.slug

        # =========================
        # Login (tenant context still active)
        # =========================

        try:

            login(
                request,
                user,
            )

        finally:
            clear_current_tenant_db()

        return redirect_by_role(user)

    return render(
        request,
        "accounts/login.html",
    )


@login_required
def doctor_dashboard(request):

    if request.user.role != User.Role.DOCTOR:
        return redirect_by_role(request.user)

    from patients.models import Patient

    today = timezone.localdate()

    patients = Patient.objects.filter(
        queue_date=today
    )

    today_patients = patients.order_by(
        "queue_number"
    )

    context = {
        "user": request.user,
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

        "today_patients": today_patients,
    }

    return render(
        request,
        "doctor/dashboard.html",
        context,
    )


@login_required
def doctor_employees(request):

    if request.user.role != User.Role.DOCTOR:
        return redirect_by_role(request.user)

    employees = (
        User.objects
        .filter(
            role=User.Role.SECRETARY
        )
        .order_by("-date_joined")
    )

    form_errors = {}
    form_data = {}

    if request.method == "POST" and "create_employee" in request.POST:

        full_name = request.POST.get(
            "full_name",
            "",
        ).strip()

        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        password_confirm = request.POST.get(
            "password_confirm",
            "",
        )

        form_data = {
            "full_name": full_name,
            "username": username,
        }

        if not full_name:
            form_errors["full_name"] = (
                "يرجى إدخال اسم الموظف."
            )

        if not username:
            form_errors["username"] = (
                "يرجى إدخال اسم المستخدم."
            )

        elif User.objects.filter(
            username=username
        ).exists():

            form_errors["username"] = (
                "اسم المستخدم موجود بالفعل."
            )

        if not password:
            form_errors["password"] = (
                "يرجى إدخال كلمة المرور."
            )

        elif len(password) < 6:
            form_errors["password"] = (
                "كلمة المرور يجب أن تكون 6 أحرف على الأقل."
            )

        elif password != password_confirm:
            form_errors["password"] = (
                "كلمات المرور غير متطابقة."
            )

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

            return redirect(
                "doctor_employees"
            )

    context = {
        "employees": employees,
        "form_errors": form_errors,
        "form_data": form_data,
    }

    return render(
        request,
        "doctor/employees.html",
        context,
    )


@login_required
def secretary_dashboard(request):

    if request.user.role != User.Role.SECRETARY:
        return redirect_by_role(request.user)

    from patients.models import Patient

    today = timezone.localdate()

    patients = Patient.objects.filter(
        queue_date=today
    )

    today_patients = patients.order_by(
        "queue_number"
    )

    context = {
        "user": request.user,
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

        "today_patients": today_patients,
    }

    return render(
        request,
        "secretary/dashboard.html",
        context,
    )


@login_required
def secretary_attendance(request):

    if request.user.role != User.Role.SECRETARY:
        return redirect_by_role(request.user)

    today = timezone.localdate()
    now = timezone.now()

    try:

        attendance = Attendance.objects.get(
            employee=request.user,
            date=today,
        )

    except Attendance.DoesNotExist:

        attendance = None

    if request.method == "POST":

        action = request.POST.get("action")

        # =========================
        # Check In
        # =========================

        if action == "check_in":

            if attendance is None:

                attendance = Attendance.objects.create(
                    employee=request.user,
                    date=today,
                    check_in=now,
                )

                messages.success(
                    request,
                    "تم تسجيل الحضور بنجاح. أتمنى لك يومًا سعيدًا!",
                )

            elif attendance.check_in is None:

                attendance.check_in = now

                attendance.save(
                    update_fields=[
                        "check_in"
                    ]
                )

                messages.success(
                    request,
                    "تم تسجيل الحضور بنجاح.",
                )

        # =========================
        # Check Out
        # =========================

        elif action == "check_out":

            if (
                attendance
                and attendance.check_in
                and attendance.check_out is None
            ):

                attendance.check_out = now

                attendance.save(
                    update_fields=[
                        "check_out"
                    ]
                )

                messages.success(
                    request,
                    f"تم تسجيل الانصراف بنجاح. مدة العمل: {attendance.work_duration}",
                )

        return redirect(
            "secretary_attendance"
        )

    recent_attendances = (
        Attendance.objects
        .filter(
            employee=request.user
        )
        .exclude(
            date=today
        )
        .order_by("-date")[:10]
    )

    context = {
        "today": today,
        "attendance": attendance,
        "recent_attendances": recent_attendances,
    }

    return render(
        request,
        "secretary/attendance.html",
        context,
    )


@login_required
def logout_view(request):

    logout(request)

    return redirect("login")