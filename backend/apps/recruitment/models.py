from django.db import models

from apps.accounts.models import HRProfile


class Job(models.Model):
    """
    Job posting — HR job create karta hai.
    Candidate isi job pe apply karega.
    """
    job_id = models.BigAutoField(primary_key=True)

    hr = models.ForeignKey(
        HRProfile,
        on_delete=models.CASCADE,
        related_name="jobs",
        db_column="hr_id",
    )

    job_title = models.CharField(max_length=200)

    job_description = models.TextField()

    required_exp = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        help_text="Required experience in years (e.g., 2.5)",
    )

    minimum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Minimum CV match score (0-100) required to proceed",
    )

    due_date = models.DateField(
        help_text="Last date to apply",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_title} (HR: {self.hr.user.full_name})"