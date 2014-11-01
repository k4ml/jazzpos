from django import forms

from xpos.forms import RequestModelForm

from jazzpos.models import Customer, Patient, Treatment, StoreSettings

DATE_FORMAT = (
    "%d-%m-%Y",
)

class CustomerForm(RequestModelForm):
    refferer = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        #self.fields['address'].label = 'Alamat'

    class Meta:
        model = Customer
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'cols': 80, }),
            'notes': forms.Textarea(attrs={'rows': 3, 'cols': 80, }),
        }

class PatientForm(RequestModelForm):

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        self.fields['dob'].label = 'Tarikh lahir'
        self.fields['dob'].input_formats = DATE_FORMAT
        self.fields['dob'].widget = forms.DateInput(format="%d-%m-%Y")

    class Meta:
        model = Patient
        exclude = ('customer', 'rcno', 'old_dob', 'nota_penting',)
        widgets = {
            'treatment_history': forms.Textarea(attrs={'rows': 3, 'cols': 80, }),
            'notes': forms.Textarea(attrs={'rows': 3, 'cols': 80, }),
        }

class TreatmentForm(RequestModelForm):
    def save(self, commit=True):
        self.instance.uid = self.request.user.id
        self.store = self.request.store
        return super(TreatmentForm, self).save(commit=commit)

    class Meta:
        model = Treatment
        exclude = ('nid', 'uid', 'type', 'created', 'modified', 'store',)
        widgets = {
            'patient': forms.HiddenInput,
            'notes': forms.Textarea(attrs={'rows': 5, 'cols': 80, }),
            'symptom': forms.Textarea(attrs={'rows': 5, 'cols': 80, }),
            'diagnosis': forms.Textarea(attrs={'rows': 5, 'cols': 80, }),
            'remedy': forms.Textarea(attrs={'rows': 5, 'cols': 80, }),
        }

class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        widgets = {
            'name': forms.HiddenInput,
            'store': forms.HiddenInput,
        }
