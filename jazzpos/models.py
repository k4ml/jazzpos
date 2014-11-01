import datetime

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

LEVEL_CHOICES = (
    ('spiritual', 'Spritual'),
    ('emositional', 'Emosi'),
    ('mental', 'Mental'),
    ('fizikal', 'Fizikal'),
)

LOG_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
)

GENDER_CHOICES = (
    ('Male', 'Lelaki'),
    ('Female', 'Perempuan'),
)

Model = models.Model

class UserProfile(Model):
    user = models.OneToOneField(User)
    store = models.ManyToManyField('Store')

    def __unicode__(self):
        return self.user.username

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class Store(Model):
    name = models.CharField(max_length=255)

    def get_settings(self):
        settings_dict = {}
        for settings in self.storesettings_set.all():
            settings_dict[settings.name] = settings.value
        return settings_dict
    settings = property(get_settings)

    def __unicode__(self):
        return self.name

class StoreSettings(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    value = models.TextField(blank=True)
    store = models.ForeignKey(Store)

    def __unicode__(self):
        return "%s-%s" % (self.store.name, self.description)

class CustomerType(Model):
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    TYPE_CHOICES = (
        (STATUS_ACTIVE, 'Aktif'),
        (STATUS_INACTIVE, 'Tidak Aktif'),
    )

    name = models.CharField(max_length=20, primary_key=True)
    description=models.CharField(max_length=255)
    status = models.IntegerField(default=1, choices=TYPE_CHOICES)

    def __unicode__(self):
        return self.description

class Customer(Model):
    name = models.CharField(max_length=255, verbose_name="Nama")
    store = models.ForeignKey(Store)
    customer_type = models.ForeignKey(CustomerType, db_column='customer_type', verbose_name='Kategori')
    address = models.TextField(blank=True)
    postcode = models.CharField(max_length=5, blank=True)
    city = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created = models.IntegerField(null=True, editable=False)
    modified = models.IntegerField(null=True, editable=False)
    created_new = models.DateTimeField(null=True, blank=True, editable=False)
    modified_new = models.DateTimeField(auto_now=True, editable=False)
    refferer = models.ForeignKey('self', null=True)
    uid = models.IntegerField(null=True, editable=False)
    nota_penting = models.TextField(blank=True, editable=False)
    
    @models.permalink
    def get_absolute_url(self):
        return ('jazzpos.views.view_customer', [str(self.id),])

    def __unicode__(self):
        return self.name

class Patient(Model):
    customer = models.OneToOneField(Customer, primary_key=True)
    icno = models.CharField(max_length=20, blank=True, verbose_name="no ic")
    rcno = models.CharField(max_length=20, blank=True, unique=True, null=True)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER_CHOICES, verbose_name="jantina")
    log = models.IntegerField(null=True, blank=True, choices=LOG_CHOICES)
    inner_level = models.CharField(max_length=20, blank=True, choices=LEVEL_CHOICES, verbose_name="warna dalaman")
    outer_level = models.CharField(max_length=20, blank=True, choices=LEVEL_CHOICES, verbose_name="warna luaran")
    mobile_phone = models.CharField(max_length=20, blank=True, verbose_name="h/p")
    postcode = models.CharField(max_length=5, blank=True, verbose_name="poskod")
    notes = models.TextField(blank=True, verbose_name="nota")
    treatment_history = models.TextField(blank=True, verbose_name="sejarah rawatan")
    dob = models.DateTimeField(null=True, blank=True, verbose_name="tarikh lahir", help_text="Format: 15-04-1981 (DD-MM-YYYY)")
    old_dob = models.IntegerField(null=True)
    nota_penting = models.CharField(max_length=255)

    def __unicode__(self):
        return self.customer.name

Customer.patient = property(lambda c: Patient.objects.get_or_create(customer=c)[0])

class Treatment(Model):
    patient = models.ForeignKey(Patient)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(null=True)
    modified = models.DateTimeField(null=True)
    uid = models.IntegerField(blank=True)
    type = models.CharField(max_length=10)
    symptom = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    remedy = models.TextField(blank=True)

    # since we need to allow editing per store
    store = models.ForeignKey(Store)

    def save(self, *args, **kwargs):
        if not self.id:
            if not self.created:
                self.created = datetime.datetime.now()
        self.modified = datetime.datetime.now()
        super(Treatment, self).save(*args, **kwargs)
