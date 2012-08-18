# -*- coding: utf-8 -*-
"""
    folivora.utils.views
    ~~~~~~~~~~~~~~~~~~~~

    Mixins for class based generic views.
"""
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from ..models import Project, ProjectMember


class SortListMixin(object):
    """This mixin allows the user to sort the queryset by predefined fields.

    This mixin is used by assigning an iterable to `sort_fields` containing
    strings which have to match the field names of the model from the
    underlying generic view.

    The default order is specified by `default_order` which has to be a string
    with the same syntax requirements as Django's `QuerySet.order_by()` method.

    Incoming requests are checked for a `sort`-GET param and verified against
    `sort_fields` before the sorting is applied.
    """
    sort_fields = None
    default_order = ('pk',)

    def get_context_data(self, **kwargs):
        context = super(SortListMixin, self).get_context_data(**kwargs)
        context.update({
            'sort_fields': self.sort_fields,
            'sort_field': self.sort_field,
            'sort_order': self.sort_order
        })
        return context

    def get_queryset(self):
        qs = super(SortListMixin, self).get_queryset()
        self.sort_field = None
        if self.sort_fields:
            sort = self.request.GET.get('sort')
            if sort and sort.strip('-') in self.sort_fields:
                self.sort_field = sort
                qs = qs.order_by(sort)
            else:
                qs = qs.order_by(*self.default_order)
                self.sort_field = self.default_order[0]
        self.sort_order = 'desc' if self.sort_field[0] == '-' else 'asc'
        self.sort_field = self.sort_field.strip('-')
        return qs


class MemberRequiredMixin(object):
    """Mixin which checks if the user has access to the project in question.

    It is written for this project and won't work anywhere else ;)

    Access is granted by checking if the user is a member of a project, the
    project is taken from the slug in the URL.

    Additionally it checks if the user is authenticated.

    Set allow_only_owner True, to grant access only to owners
    """
    allow_only_owner = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs['slug']
        project = Project.objects.get(slug=slug)
        query = ProjectMember.objects.filter(user=request.user, project=project)
        if self.allow_only_owner:
            query = query.filter(state=ProjectMember.OWNER)
        if not query.exists():
            return HttpResponseForbidden('403 - Forbidden')
        return super(MemberRequiredMixin, self).dispatch(request, *args, **kwargs)
