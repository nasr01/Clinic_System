from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        DOCTOR = "doctor", "طبيب"
        SECRETARY = "secretary", "سكرتير"

    full_name = models.CharField(
        max_length=150,
        verbose_name="الاسم الكامل",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        verbose_name="الدور",
    )

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

        constraints = [
            models.UniqueConstraint(
                fields=["username"],
                name="unique_username",
            )
        ]

    def __str__(self):
        return self.full_name or self.username


class Attendance(models.Model):

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="الموظف",
    )

    date = models.DateField(
        verbose_name="التاريخ",
    )

    check_in = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت الحضور",
    )

    check_out = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت الانصراف",
    )

    class Meta:
        ordering = ["-date", "-check_in"]

        verbose_name = "حضور"
        verbose_name_plural = "الحضور والانصراف"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"],
                name="unique_daily_attendance_per_employee",
            )
        ]

    def __str__(self):
        return f"{self.employee} - {self.date}"

    @property
    def work_duration(self):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in

            total_seconds = int(
                delta.total_seconds()
            )

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60

            return f"{hours} س و {minutes} د"

        return "-"