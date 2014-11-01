from django.shortcuts import redirect

from .forms import FormRedirectException

class FormRedirectMiddleware:
    def process_exception(self, request, exception):
        if isinstance(exception, FormRedirectException):
            return redirect(*exception.args, **exception.kwargs)
        return None
