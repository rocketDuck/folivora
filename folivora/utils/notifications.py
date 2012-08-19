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
    """Route notifications to specific endpoints depending on their log action.

    :param log_entries: All log entries where notifications needs to be routed.
    """
    for entry in log_entries:
        if entry.action in ACTION_MAPPING:
            ACTION_MAPPING[entry.action](entry)


def send_update_avilable_notification(log):
    """Send a notification to all project members that are affected by `log`.

    :param log: Log model that holds information for the notification.
    """
    msg = loader.render_to_string('notifications/update_available.mail.txt',
                                  {'log': log})
    subject = '{prefix}New update available for project "{project}"'.format(**{
        'prefix': settings.EMAIL_SUBJECT_PREFIX,
        'project': log.project.name})

    mails = []
    members = log.project.projectmember_set.all()
    for member in members:
        mails.append(member.mail or member.user.email)

    send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, mails,
              fail_silently=False)


ACTION_MAPPING = {
    'update_available': send_update_avilable_notification
}
