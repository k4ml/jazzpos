# Create your views here.
from django.core.urlresolvers import reverse
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.views import logout_then_login
from django.contrib.auth.views import password_change as auth_password_change, \
    password_change_done as auth_password_change_done
from django.contrib.auth.decorators import login_required

from kecupuapp_base.shortcuts import render_response 

def login(request):
    return auth_login(request, template_name='kecupuapp_base/login.html')

def logout(request):
    login_url = reverse('kecupuapp_base:login')
    return logout_then_login(request, login_url=login_url)

@login_required
def profile(request):
    return render_response(request, 'kecupuapp_base/profile.html')

def password_change(request, *args, **kwargs):
    return auth_password_change(
        request,
        template_name='kecupuapp_base/password_change_form.html',
        post_change_redirect=reverse('kecupuapp_base:password-change-done'),
    )

def password_change_done(request, *args, **kwargs):
    return auth_password_change_done(
        request,
        template_name='kecupuapp_base/password_change_done.html',
    )
