import datetime

from django import forms

class TextSearchForm(forms.Form):
    q = forms.CharField()

class DateSearchForm(forms.Form):
    DATE_FORMAT = ('%d-%m-%Y',)
    date_start = forms.DateField(required=False, input_formats=DATE_FORMAT)
    date_end = forms.DateField(required=False, input_formats=DATE_FORMAT)

    def xclean_date_start(self):
        data = self.cleaned_data['date_start']
        if data is None:
            return datetime.datetime.now()

        return data

    def xclean_date_end(self):
        data = self.cleaned_data['date_end']
        if data is None:
            return datetime.datetime.now()

        return data

    def clean(self):
        if any(self.errors):
            return

        date_start = self.cleaned_data['date_start']
        date_end = self.cleaned_data['date_end']

        if date_start is not None and date_end is None:
            raise forms.ValidationError('Date end required')

        if date_end is not None and date_start is None:
            raise forms.ValidationError('Date start required')

        return self.cleaned_data
