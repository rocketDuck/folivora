import re
from django.conf import settings


# NOTE: according to rfc4622 a nodeid is optional. But we require one
# 'cause nobody should enter a service-jid in the jabber field.
# That way we don't need to validate the domain and resid.
_jabber_re = re.compile(r'(?xi)(?:[a-z0-9!$\(\)*+,;=\[\\\]\^`{|}\-._~]+)@')


def is_valid_jid(jabber):
    return _jabber_re.match(jabber) is not None
