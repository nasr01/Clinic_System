from django.urls import path

from .views import (
    doctor_dashboard,
    doctor_employees,
    login_view,
    logout_view,
    secretary_attendance,
    secretary_dashboard,
)


urlpatterns = [
    path("login/", login_view, name="login"),
    path(
        "doctor/dashboard/",
        doctor_dashboard,
        name="doctor_dashboard",
    ),
    path(
        "doctor/employees/",
        doctor_employees,
        name="doctor_employees",
    ),
    path(
        "secretary/dashboard/",
        secretary_dashboard,
        name="secretary_dashboard",
    ),
    path(
        "secretary/attendance/",
        secretary_attendance,
        name="secretary_attendance",
    ),
    path("logout/", logout_view, name="logout"),
]
