import urllib
import hashlib
from datetime import datetime

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.timezone import make_aware, utc

register = template.Library()

@register.filter
def gravatar_url(email, size):
    size = str(size)
    gravatar_url = 'http://www.gravatar.com/avatar.php?'
    gravatar_url += urllib.urlencode({
        'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
        'size':str(size)
    })
    return gravatar_url


@stringfilter
@register.filter
def parse_iso_datetime(value):
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return make_aware(dt, utc)
