from django.conf.urls.defaults import *
from django.template import add_to_builtins

add_to_builtins('kecupuapp_base.templatetags.base_filters')

# URL patterns for kecupu.base

urlpatterns = patterns('kecupuapp_base.views',
    # Add url patterns here
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^profile/password/change/$', 'password_change', name='password-change'),
    url(r'^profile/password/change-done/$', 'password_change_done', name='password-change-done'),
)
