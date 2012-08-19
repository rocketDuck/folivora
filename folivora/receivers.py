from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in

from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(user_logged_in)
def set_user_lang(sender, request, user, **kwargs):
    try:
        profile = user.get_profile()
        if profile.language:
            request.session['django_language'] = profile.language
        if profile.timezone:
            request.session['django_timezone'] = profile.timezone
    except UserProfile.DoesNotExist:
        pass
