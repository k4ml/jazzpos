"""
This would be abandon for now until I know a better way 
to use class based views safely.
"""

from django.http import HttpResponse
from django.template import add_to_builtins

class BaseSite:

    def __init__(self, name=None, app_name='kecupuapp_base'):
        if name is None:
            self.name = 'kecupuapp_base'
        else:
            self.name = name
        self.app_name = name

    def login(self, request):
        from django.contrib.auth.views import login
        return login(request, template_name='kecupuapp_base/login.html')

    def logout(self, request):
        from django.contrib.auth.views import logout_then_login
        return logout_then_login(request)

    def profile(self, request):
        from kecupuapp_base.shortcuts import render_response 
        return render_response(request, 'kecupuapp_base/profile.html')

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url, include

        urlpatterns = patterns('',
            url(r'^login/$', self.login, name='login'),
            url(r'^logout/$', self.logout, name='logout'),
            url(r'^profile/$', self.profile, name='profile'),
        )

        return urlpatterns

    def urls(self):
        return self.get_urls(), self.app_name, self.name
    urls = property(urls)
    
basesite = BaseSite()

# add base_filters to all templates instead of calling
# {% load base_filters %} in each templates.
add_to_builtins('kecupuapp_base.templatetags.base_filters')
