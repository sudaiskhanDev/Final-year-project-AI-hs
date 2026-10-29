from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, HRProfile, CandidateProfile


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """
    Jab bhi naya User bane (kisi bhi source se — register, admin panel, shell),
    uske role ke hisaab se empty profile automatically create ho jaye.
    """
    if not created:
        return

    # Superuser / is_staff (Django admin) ke liye koi profile nahi
    if instance.is_superuser or instance.is_staff:
        return

    if instance.role == "hr":
        HRProfile.objects.get_or_create(
            user=instance,
            defaults={
                "department": "",
                "designation": "",
            },
        )

    elif instance.role == "candidate":
        CandidateProfile.objects.get_or_create(
            user=instance,
        )