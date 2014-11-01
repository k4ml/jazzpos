import pdb, functools

from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

class InvalidRole(Exception):
    pass

def has_role(role):
    valid_roles = ('staff', 'superuser')
    if role not in valid_roles:
        raise InvalidRole
    role = 'is_%s' % role
    def actual_decorator(views_func):
        def views_func_wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated():
                login_url = '%s?next=%s' % (reverse('kecupuapp_base:login'), 
                                            request.path)
                return HttpResponseRedirect(login_url)

            tests = {
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            }
            if tests[role]:
                return views_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()
        return functools.wraps(views_func)(views_func_wrapper)
    return actual_decorator
