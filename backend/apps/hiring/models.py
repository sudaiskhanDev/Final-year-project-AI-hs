from django.db import models

from apps.recruitment.models import Application


class ResumeMatching(models.Model):
    """
    CV vs Job Description match scoring.
    Jab candidate apply karta hai, system is table mein scores save karta hai.
    """
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    matching_id = models.BigAutoField(primary_key=True)

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="resume_matching",
        db_column="application_id",
    )

    skills_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Skills match score (0-100)",
    )

    experience_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Experience match score (0-100)",
    )

    qualification_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Qualification match score (0-100)",
    )

    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Weighted total score (0-100)",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    evaluated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "resume_matching"
        ordering = ["-matching_id"]

    def __str__(self):
        return f"App #{self.application.application_id} - {self.total_score} ({self.status})"








class AIInterview(models.Model):
    """
    Interview session — candidate ka interview.
    Video record hoti hai, questions poochhe jaate hain, scores assign hote hain.
    """
    MODE_CHOICES = (
        ("ai", "AI"),
        ("human", "Human"),
        ("video", "Video"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    interview_id = models.BigAutoField(primary_key=True)

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews",
        db_column="application_id",
    )

    interview_mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default="ai",
    )

    interview_round = models.CharField(
        max_length=50,
        default="1st Round",
        help_text="e.g., 1st Round, 2nd Round, Technical",
    )

    video_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to recorded video",
    )

    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Overall interview score (0-100)",
    )

    interview_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    started_at = models.DateTimeField(blank=True, null=True)

    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "ai_interviews"
        ordering = ["-interview_id"]

    def __str__(self):
        return f"App #{self.application.application_id} - {self.interview_round} ({self.interview_status})"
    







class Question(models.Model):
    """
    Interview ke andar poochhe gaye questions aur unke answers.
    Har interview ke multiple questions ho sakte hain.
    """
    question_id = models.BigAutoField(primary_key=True)

    interview = models.ForeignKey(
        AIInterview,
        on_delete=models.CASCADE,
        related_name="questions",
        db_column="interview_id",
    )

    question_text = models.TextField()

    answer_text = models.TextField(
        blank=True,
        null=True,
        help_text="Candidate ka jawab (text form mein)",
    )

    answer_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Answer score (0-100)",
    )

    time_taken = models.IntegerField(
        default=0,
        help_text="Time taken to answer (in seconds)",
    )

    class Meta:
        db_table = "question"
        ordering = ["question_id"]

    def __str__(self):
        return f"Q#{self.question_id} - Interview #{self.interview.interview_id} (score: {self.answer_score})"