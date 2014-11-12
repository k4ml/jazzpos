from django.http import HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.views.generic import create_update
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q

from kecupuapp_base.shortcuts import render_response
from kecupuapp_base.decorators import has_role
from kecupuapp_base.forms import process_form

from haystack.query import SearchQuerySet
from haystack.views import basic_search

from cari.forms import TextSearchForm

from jazzpos.models import Customer, Store, Patient, Treatment, StoreSettings
from jazzpos.forms import CustomerForm, PatientForm, TreatmentForm, StoreSettingsForm
from xpos.views import main as xpos_views

from gfbv import list_detail

@has_role('staff')
def index(request):
    return render_response(request, 'index.html')

@has_role('staff')
def list_customers(request):
    ctx = {}
    qs = Customer.objects.all()

    if request.GET.get('q', None) is not None:
        form = TextSearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            qs = qs.filter(Q(name__icontains=q) | Q(patient__icno=q))

    ctx['customer_list'] = qs.order_by('-id')

    return render_response(
        request,
        'jazzpos/customer_list.html',
        ctx
    )

@has_role('staff')
def add_customer(request):
    ctx = {}
    redirect_to = reverse('jazzpos.views.list_customers')
    initial = {
        'store': request.session['store_id'],
        'customer_type': 'patient',
    }
    ctx['form'] = process_form(request, CustomerForm, initial=initial, redirect_to=redirect_to)
    return render_response(
        request,
        'customer_add.html',
        ctx
    )

@has_role('staff')
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    # allow only customer own store except for admin
    if not request.user.is_superuser:
        if customer.store != request.store:
            return HttpResponseForbidden()

    ctx = {}
    redirect_to = reverse('jazzpos.views.view_customer', args=(customer_id,))
    initial = {
        'store': request.session['store_id'],
    }
    ctx['form'] = process_form(request, CustomerForm, initial=initial, redirect_to=redirect_to, instance=customer)
    ctx['customer'] = customer
    return render_response(
        request,
        'customer_edit.html',
        ctx
    )

@has_role('staff')
def edit_patient(request, customer_id):
    patient = get_object_or_404(Patient, customer=customer_id)

    # allow only customer own store except for admin
    if not request.user.is_superuser:
        if patient.customer.store != request.store:
            return HttpResponseForbidden()

    ctx = {}
    redirect_to = reverse('jazzpos.views.view_customer', args=(customer_id,))
    initial = {
        'store': request.session['store_id'],
    }
    ctx['form'] = process_form(request, PatientForm, initial=initial, redirect_to=redirect_to, instance=patient)
    ctx['patient'] = patient
    return render_response(
        request,
        'patient_edit.html',
        ctx
    )

@has_role('staff')
def view_customer(request, customer_id):
    return list_detail.object_detail(
        request,
        queryset=Customer.objects.all(),
        object_id=customer_id,
        template_name='customer_detail.html',
        template_object_name='customer',
    )

def list_treatments(request, customer_id):
    ctx = {}
    patient = get_object_or_404(Patient, customer=customer_id) 
    ctx['patient'] = patient
    ctx['treatments'] = patient.treatment_set.all().order_by('-id')
    return render_response(
        request,
        'treatment_list.html',
        ctx
    )

@has_role('staff')
def edit_treatment(request, treatment_id):
    treatment = get_object_or_404(Treatment, pk=treatment_id)

    # allow only customer own store except for admin
    if not request.user.is_superuser:
        if treatment.store != request.store:
            return HttpResponseForbidden()

    ctx = {}
    redirect_to = reverse('jazzpos.views.list_treatments', args=(treatment.patient.customer_id,))
    initial = {
        'store': request.session['store_id'],
    }
    ctx['form'] = process_form(request, TreatmentForm, initial=initial, redirect_to=redirect_to, instance=treatment)
    ctx['treatment'] = treatment
    ctx['patient'] = treatment.patient
    ctx['action'] = 'Edit'
    return render_response(
        request,
        'treatment_edit.html',
        ctx
    )

@has_role('staff')
def add_treatment(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    ctx = {}
    redirect_to = reverse('jazzpos.views.list_treatments', args=(patient.customer_id,))
    initial = {
        'store': request.session['store_id'],
        'patient': patient,
    }
    ctx['form'] = process_form(request, TreatmentForm, initial=initial, redirect_to=redirect_to)
    ctx['patient'] = patient
    ctx['action'] = 'Tambah'
    return render_response(
        request,
        'treatment_edit.html',
        ctx
    )

@has_role('staff')
def list_orders(request, customer_id):
    return xpos_views.list_orders(request, customer_id)

@has_role('staff')
def add_order(request, customer_id):
    return create_update.create_object(
        request,
        model=Order,
        post_save_redirect=reverse('jazzpos.views.list_customers'),
        template_name='customer_add.html',
    )

def switch_store(request, store_id=None):
    try:
        store_id = int(store_id)
    except:
        store_id = None

    if store_id is None:
        return render_response(
            request,
            'stores_switch.html',
        )

    store = get_object_or_404(Store, pk=store_id)
    redirect_to = request.GET.get('redirect_to', '/')
    request.session['store_id'] = store.id
    return redirect(redirect_to)

@has_role('staff')
def store_settings(request, object_id=None):
    if object_id:
        return create_update.update_object(
            request,
            form_class=StoreSettingsForm,
            object_id=object_id,
            post_save_redirect=reverse('jazzpos-store-settings'),
        )
    
    return list_detail.object_list(
        request,
        queryset=StoreSettings.objects.filter(store=request.store),
    )
