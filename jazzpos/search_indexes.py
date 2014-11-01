from haystack import indexes
from haystack import site

from jazzpos.models import Customer, Patient

class CustomerIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

class PatientIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

site.register(Customer, CustomerIndex)
site.register(Patient, PatientIndex)
