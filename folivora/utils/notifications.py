# -*- coding: utf-8 -*-
"""
    folivora.utils.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Framework for user/project notifications.
"""
from django.conf import settings
from django.template import loader
from django.core.mail import send_mail


def route_notifications(*log_entries):
    for entry in log_entries:
        if entry.action in ACTION_MAPPING:
            ACTION_MAPPING[entry.action](entry)



def send_update_avilable_notification(log):
    message = loader.render_to_string('notifications/update_available.mail.txt',
                                      {'log': log})
    subject = '{prefix}New update available for project "{project}"'.format(**{
        'prefix': settings.EMAIL_SUBJECT_PREFIX,
        'project': log.project.name})

    emails = log.project.members.values_list('email', flat=True)

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails,
              fail_silently=False)



ACTION_MAPPING = {
    'update_available': send_update_avilable_notification
}
