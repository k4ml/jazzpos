from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django_tablib.admin import TablibAdmin

from jazzpos.models import Customer, Patient, Store, CustomerType, StoreSettings
from jazzpos.models import UserProfile

class CustomerAdmin(TablibAdmin):
    formats = ['xls', 'csv',]

class PatientAdmin(TablibAdmin):
    formats = ['xls', 'csv',]

class StoreAdmin(admin.ModelAdmin):
    pass

class StoreSettingsAdmin(admin.ModelAdmin):
    pass

class CustomerTypeAdmin(admin.ModelAdmin):
    pass

class UserProfileInline(admin.StackedInline):
    model = UserProfile

UserAdmin.inlines = [UserProfileInline,]

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(StoreSettings, StoreSettingsAdmin)
admin.site.register(CustomerType, CustomerTypeAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
