from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "age", "phone"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "اسم المريض",
                }
            ),
            "age": forms.NumberInput(
                attrs={
                    "placeholder": "العمر",
                    "min": 1,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "رقم الهاتف",
                }
            ),
        }