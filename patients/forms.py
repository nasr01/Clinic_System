from django import forms
from django.utils import timezone

from .models import Patient, PatientAttachment, PatientNote


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "age", "phone", "visit_type", "complaint"]

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
            "visit_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "complaint": forms.Textarea(
                attrs={
                    "placeholder": "المرض أو الشكوى الرئيسية للمريض...",
                    "rows": 4,
                }
            ),
        }

        labels = {
            "name": "اسم المريض",
            "age": "العمر",
            "phone": "رقم الهاتف",
            "visit_type": "نوع الزيارة",
            "complaint": "المرض / الشكوى الرئيسية",
        }


class DoctorPatientFileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "age", "phone", "complaint"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "اسم المريض الكامل",
                    "class": "form-input",
                }
            ),
            "age": forms.NumberInput(
                attrs={
                    "placeholder": "مثال: 30",
                    "min": 1,
                    "max": 150,
                    "class": "form-input",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "مثال: 05xxxxxxxx",
                    "class": "form-input",
                    "style": "direction:ltr;unicode-bidi:embed;text-align:right;",
                }
            ),
            "complaint": forms.Textarea(
                attrs={
                    "placeholder": "وصف المرض أو الشكوى الرئيسية للمريض...",
                    "rows": 4,
                    "class": "form-input",
                }
            ),
        }

        labels = {
            "name": "اسم المريض *",
            "age": "السن *",
            "phone": "رقم الهاتف",
            "complaint": "المرض / الشكوى الرئيسية",
        }

    def save(self, commit=True, **kwargs):
        from django.db.models import Max

        instance = super().save(commit=False)

        today = timezone.localdate()
        last_queue = (
            Patient.objects.filter(queue_date=today)
            .aggregate(Max("queue_number"))["queue_number__max"]
        )

        instance.queue_date = today
        instance.queue_number = (last_queue or 0) + 1
        instance.status = Patient.Status.WAITING
        instance.visit_type = Patient.VisitType.EXAMINATION
        instance.has_file = True
        instance.file_created_at = timezone.now()

        if commit:
            instance.save()
        return instance


class PatientNoteForm(forms.ModelForm):
    class Meta:
        model = PatientNote
        fields = ["title", "content", "visit_date"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "عنوان الملاحظة (اختياري: مثلاً زيارة متابعة)",
                    "class": "form-input",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "اكتب هنا الملاحظات أو التشخيص أو الوصفة...",
                    "rows": 6,
                    "class": "form-input",
                }
            ),
            "visit_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-input",
                },
                format="%Y-%m-%d",
            ),
        }

        labels = {
            "title": "عنوان الملاحظة",
            "content": "الملاحظة / التشخيص *",
            "visit_date": "تاريخ الزيارة *",
        }


class PatientAttachmentForm(forms.ModelForm):
    class Meta:
        model = PatientAttachment
        fields = ["file", "caption"]

        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-input",
                    "accept": "image/*,.pdf,.doc,.docx,.txt",
                }
            ),
            "caption": forms.TextInput(
                attrs={
                    "placeholder": "وصف الملف (مثال: تحليل دم، صورة أشعة...)",
                    "class": "form-input",
                }
            ),
        }

        labels = {
            "file": "الملف / الصورة *",
            "caption": "وصف الملف",
        }
