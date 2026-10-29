from django.db import models


class Skill(models.Model):
    """
    Master list of skills (Python, Java, React, SQL, etc.)
    Candidate aur Job dono isi se reference karte hain.
    """
    skill_id = models.BigAutoField(primary_key=True)
    skill_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "skills"
        ordering = ["skill_name"]

    def __str__(self):
        return self.skill_name


class Qualification(models.Model):
    """
    Master list of qualifications (BSCS, MSCS, BBA, MBA, etc.)
    """
    qualification_id = models.BigAutoField(primary_key=True)
    qualification_name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "qualification"
        ordering = ["qualification_name"]

    def __str__(self):
        return self.qualification_name


class Language(models.Model):
    """
    Master list of languages (English, Urdu, Arabic, etc.)
    """
    lang_id = models.BigAutoField(primary_key=True)
    language_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "languages"
        ordering = ["language_name"]

    def __str__(self):
        return self.language_name