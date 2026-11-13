import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction

from apps.accounts.models import CandidateProfile
from apps.candidates.models import Resume
from apps.recruitment.models import Application, Job


@transaction.atomic
def apply_for_job(candidate_id, job_id, uploaded_file=None, resume_id=None):
    """
    Atomic workflow: Resume + Application save in ONE transaction.

    Modes:
      1. New file uploaded -> create Resume + Application
      2. Existing resume_id -> use that Resume for Application

    Raises:
      ValueError: for validation errors (400)
    """

    # 1. Validate candidate
    try:
        candidate = CandidateProfile.objects.get(pk=candidate_id)
    except CandidateProfile.DoesNotExist:
        raise ValueError("Candidate profile not found")

    # 2. Validate job
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        raise ValueError("Job not found")

    # 3. Duplicate check BEFORE saving any resume (avoid orphan)
    if Application.objects.filter(candidate=candidate, job=job).exists():
        raise ValueError("You have already applied for this job")

    # 4. Resume handling
    resume = None

    if uploaded_file:
        # Validate extension
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in [".pdf", ".docx"]:
            raise ValueError("Only PDF and DOCX files are allowed")

        # Save file to media/resumes/
        save_path = os.path.join("resumes", uploaded_file.name)
        saved_path = default_storage.save(save_path, ContentFile(uploaded_file.read()))
        file_url = settings.MEDIA_URL + saved_path

        resume = Resume.objects.create(
            candidate=candidate,
            file_name=uploaded_file.name,
            file_path=file_url,
        )

    elif resume_id:
        try:
            resume = Resume.objects.get(pk=resume_id, candidate=candidate)
        except Resume.DoesNotExist:
            raise ValueError("Resume not found or does not belong to you")

    else:
        raise ValueError("Either file or resume_id is required")

    # 5. Create application
    application = Application.objects.create(
        candidate=candidate,
        job=job,
        resume=resume,
        application_status="applied",
    )

    return {
        "application_id": application.application_id,
        "resume_id": resume.resume_id,
        "job_id": job.job_id,
        "application_status": application.application_status,
        "applied_at": application.applied_at,
    }