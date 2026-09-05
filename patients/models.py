import os
import uuid

from django.db import models
from django.utils import timezone


def patient_attachment_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    date_path = timezone.localdate().strftime("%Y/%m/%d")
    return f"patient_attachments/{date_path}/{safe_name}"


class Patient(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "في الانتظار"
        IN_EXAMINATION = "in_examination", "جاري الكشف"
        COMPLETED = "completed", "تم الكشف"

    class VisitType(models.TextChoices):
        EXAMINATION = "examination", "كشف"
        CONSULTATION = "consultation", "استشارة"

    name = models.CharField(max_length=150)

    age = models.PositiveIntegerField()

    phone = models.CharField(max_length=20)

    queue_date = models.DateField()

    queue_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.WAITING,
    )

    visit_type = models.CharField(
        max_length=20,
        choices=VisitType.choices,
        default=VisitType.EXAMINATION,
        verbose_name="نوع الزيارة",
    )

    complaint = models.TextField(
        blank=True,
        default="",
        verbose_name="المرض / الشكوى الرئيسية",
    )

    has_file = models.BooleanField(
        default=False,
        verbose_name="لديه ملف مريض",
        help_text="إذا كان True يظهر في سجل ملف المرضى لدى الدكتور",
    )

    file_created_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ إنشاء الملف",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    examination_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["queue_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["queue_date", "queue_number"],
                name="unique_daily_queue_number",
            )
        ]

    def __str__(self):
        return f"#{self.id} - {self.name} ({self.age} سنة)"


class PatientNote(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="المريض",
    )

    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_notes",
        verbose_name="الدكتور",
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="عنوان الملاحظة",
    )

    content = models.TextField(
        verbose_name="الملاحظة / التشخيص",
    )

    visit_date = models.DateField(
        default=timezone.localdate,
        verbose_name="تاريخ الزيارة",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date", "-created_at"]
        verbose_name = "ملاحظة مريض"
        verbose_name_plural = "ملاحظات المرضى"

    def __str__(self):
        header = self.title or "ملاحظة عامة"
        return f"[{self.patient.id}] {self.patient.name} - {header} ({self.visit_date})"


class PatientAttachment(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="المريض",
    )

    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_attachments",
        verbose_name="رفع بواسطة",
    )

    file = models.FileField(
        upload_to=patient_attachment_upload_path,
        verbose_name="الملف / الصورة",
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="وصف الملف",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "مرفق مريض"
        verbose_name_plural = "مرفقات المرضى"

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def is_image(self):
        if not self.file:
            return False
        name = self.file.name.lower()
        return any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))

    def __str__(self):
        return f"[{self.patient.id}] {self.caption or self.filename}"


class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_PATIENT = "new_patient", "مريض جديد"
        PATIENT_STARTED = "patient_started", "بدء الكشف"
        PATIENT_COMPLETED = "patient_completed", "إنهاء الكشف"
        ATTENDANCE = "attendance", "حضور وانصراف"

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="المستلم",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        verbose_name="نوع الإشعار",
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان الإشعار",
    )

    message = models.TextField(
        verbose_name="محتوى الإشعار",
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="المريض",
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="تم القراءة",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name|default:self.recipient.username}"