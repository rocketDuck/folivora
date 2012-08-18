from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from ..models import Project


class SortListMixin(object):
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
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs['slug']
        if not Project.objects.filter(members=request.user).exists():
            return HttpResponseForbidden('403 - Forbidden')
        return super(MemberRequiredMixin, self).dispatch(request, *args, **kwargs)
