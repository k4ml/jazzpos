from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('jazzpos.views',
    (r'^admin/', include(admin.site.urls)),
    (r'^$', 'index'),
    (r'^accounts/', include('kecupuapp_base.urls', namespace='kecupuapp_base', app_name='kecupuapp_base')),
    url(r'^customers/$', 'list_customers', name='jazzpos-list-customers'),
    (r'^customer/(\d+)/$', 'view_customer'),
    (r'^customer/new/$', 'add_customer'),
    (r'^customer/(\d+)/orders/$', 'list_orders'),
    (r'^customer/(\d+)/edit/$', 'edit_customer'),
    (r'^customer/(\d+)/edit/patient/$', 'edit_patient'),
    (r'^customer/(\d+)/patient/treatments/$', 'list_treatments'),
    (r'^customer/(\d+)/order/new/$', 'add_order'),
    (r'^treatment/(\d+)/edit/$', 'edit_treatment'),
    (r'^treatment/(\d+)/new/$', 'add_treatment'),
    url(r'^store/switch/(\d+)/', 'switch_store', name='jazzpos-store-switch'),
    url(r'^store/switch/', 'switch_store', name='jazzpos-store-switch-all'),
    (r'^pos/', include('xpos.urls')),
    (r'^search/', include('haystack.urls')),
    url(r'^store/settings/$', 'store_settings', name='jazzpos-store-settings'),
    url(r'^store/settings/(\d+)/$', 'store_settings', name='jazzpos-store-settings-edit'),
)

urlpatterns += patterns('xpos.views.main',
    (r'^customer/(\d+)/statements/', 'view_statement'),
)

urlpatterns += patterns('haystack.views',
    (r'^search/$', 'basic_search'),
)

urlpatterns += patterns('',
    url(r'^users/', include('smartmin.users.urls')),
)

from autocomplete.views import autocomplete
autocomplete.autodiscover()
urlpatterns += patterns('',
    url('^autocomplete/', include(autocomplete.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': settings.STATIC_ROOT}),
    )
