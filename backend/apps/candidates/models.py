from django.db import models

from apps.accounts.models import CandidateProfile
from apps.masterdata.models import Skill,Qualification ,Language


# Create your models here.



class Resume(models.Model):
    """
    Candidate ki uploaded CV/resume files.
    Ek candidate ke multiple resumes ho sakte hain.
    """
    resume_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="resumes",
        db_column="candidate_id",
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resume"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.file_name} (candidate_id={self.candidate.candidate_id})"



class CandExperience(models.Model):
    """
    Candidate ka work experience.
    Ek candidate ke multiple experiences ho sakte hain.
    """
    exp_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="experiences",
        db_column="candidate_id",
    )
    company_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)  # null = current job

    class Meta:
        db_table = "cand_experience"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.designation} @ {self.company_name}"




class CandidateSkill(models.Model):
    """
    Candidate ki skills (junction table — Candidate <-> Skill).
    Ek candidate ke multiple skills, ek skill multiple candidates ke paas.
    """
    candidate_skill_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="skills",
        db_column="candidate_id",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="candidates",
        db_column="skill_id",
    )

    class Meta:
        db_table = "candidate_skill"
        unique_together = ("candidate", "skill")
        ordering = ["candidate"]

    def __str__(self):
        return f"{self.candidate} - {self.skill.skill_name}"




class CandidateQualification(models.Model):
    """
    Candidate ki qualifications (junction table — Candidate <-> Qualification).
    """
    cq_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="qualifications",
        db_column="candidate_id",
    )
    qualification = models.ForeignKey(
        Qualification,
        on_delete=models.CASCADE,
        related_name="candidates",
        db_column="qualification_id",
    )

    class Meta:
        db_table = "candidate_qualification"
        unique_together = ("candidate", "qualification")
        ordering = ["candidate"]

    def __str__(self):
        return f"{self.candidate} - {self.qualification.qualification_name}"





class CandLanguage(models.Model):
    """
    Candidate ki languages with proficiency level (junction table — Candidate <-> Language).
    """
    PROFICIENCY_CHOICES = (
        ("basic", "Basic"),
        ("intermediate", "Intermediate"),
        ("fluent", "Fluent"),
        ("native", "Native"),
    )

    cand_lang_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="languages",
        db_column="candidate_id",
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="candidates",
        db_column="lang_id",
    )
    proficiency_lvl = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        default="intermediate",
    )

    class Meta:
        db_table = "cand_languages"
        unique_together = ("candidate", "language")
        ordering = ["candidate"]

    def __str__(self):
        return f"{self.candidate} - {self.language.language_name} ({self.proficiency_lvl})"