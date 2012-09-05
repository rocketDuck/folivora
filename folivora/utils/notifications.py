# -*- coding: utf-8 -*-
"""
    folivora.utils.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Framework for user/project notifications.
"""
from django.conf import settings
from django.template import loader
from django.core.mail import send_mail
from django.utils.translation import ugettext as _


def send_notifications(project, log_entries):
    """Send notifications for one project.

    :project: The project to send notifications for.
    :param log_entries: log entries to be sent.
    """
    rendered_entries = []
    for entry in log_entries:
        if entry.action in TEMPLATE_MAPPING:
            tmpl = TEMPLATE_MAPPING[entry.action]
            msg = loader.render_to_string(tmpl, {'log': entry})
            rendered_entries.append(msg)

    subject_tmpl = _('{prefix}New updates available for project "{project}"')
    subject = subject_tmpl.format(**{'prefix': settings.EMAIL_SUBJECT_PREFIX,
                             'project': project.name})
    body = ''.join(rendered_entries)

    mails = []
    members = project.projectmember_set.all()

    for member in members:
        mails.append(member.mail or member.user.email)

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, mails,
              fail_silently=False)


TEMPLATE_MAPPING = {
    'update_available': 'notifications/update_available.mail.txt',
}
