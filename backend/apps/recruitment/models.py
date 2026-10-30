from django.db import models

from apps.accounts.models import HRProfile, CandidateProfile
from apps.masterdata.models import Skill, Qualification

from apps.candidates.models import Resume

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





class JobSkill(models.Model):
    """
    Job ke required skills (junction table — Job <-> Skill).
    HR job post karte waqt required skills add karta hai.
    """
    job_skill_id = models.BigAutoField(primary_key=True)

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="skills",
        db_column="job_id",
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="jobs",
        db_column="skill_id",
    )

    class Meta:
        db_table = "job_skills"
        unique_together = ("job", "skill")
        ordering = ["job"]

    def __str__(self):
        return f"{self.job.job_title} - {self.skill.skill_name}"






class JobQualification(models.Model):
    """
    Job ki required qualifications (junction table — Job <-> Qualification).
    HR job post karte waqt required qualifications add karta hai.
    """
    job_qualification_id = models.BigAutoField(primary_key=True)

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="qualifications",
        db_column="job_id",
    )

    qualification = models.ForeignKey(
        Qualification,
        on_delete=models.CASCADE,
        related_name="jobs",
        db_column="qualification_id",
    )

    class Meta:
        db_table = "job_qualification"
        unique_together = ("job", "qualification")
        ordering = ["job"]

    def __str__(self):
        return f"{self.job.job_title} - {self.qualification.qualification_name}"
    






class Application(models.Model):
    """
    Candidate ki job application.
    Ek candidate ek job pe ek hi baar apply kar sakta hai.
    """
    STATUS_CHOICES = (
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("hired", "Hired"),
    )

    application_id = models.BigAutoField(primary_key=True)

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="applications",
        db_column="candidate_id",
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
        db_column="job_id",
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
        db_column="resume_id",
        help_text="Which resume was submitted with this application",
    )

    application_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied",
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "applications"
        unique_together = ("candidate", "job")  # ek job pe ek hi application
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.user.full_name} → {self.job.job_title} ({self.application_status})"