from django.urls import path

from .views import (
    add_patient,
    complete_examination,
    doctor_patients,
    secretary_patients,
    start_examination,
)


urlpatterns = [
    # Secretary
    path(
        "patients/",
        secretary_patients,
        name="secretary_patients",
    ),

    path(
        "patients/add/",
        add_patient,
        name="add_patient",
    ),

    # Doctor
    path(
        "doctor/patients/",
        doctor_patients,
        name="doctor_patients",
    ),

    path(
        "doctor/patients/<int:patient_id>/start/",
        start_examination,
        name="start_examination",
    ),

    path(
        "doctor/patients/<int:patient_id>/complete/",
        complete_examination,
        name="complete_examination",
    ),
]