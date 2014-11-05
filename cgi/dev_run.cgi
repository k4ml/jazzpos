#!/usr/bin/python

import os
import sys
import site
import wsgiref.handlers

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, PROJECT_ROOT)

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'jazzpos.settings'

application = WSGIHandler()
wsgiref.handlers.CGIHandler().run(application)
