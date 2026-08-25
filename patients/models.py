from django.db import models


class Patient(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "في الانتظار"
        IN_EXAMINATION = "in_examination", "جاري الكشف"
        COMPLETED = "completed", "تم الكشف"

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
        return f"#{self.queue_number} - {self.name}"