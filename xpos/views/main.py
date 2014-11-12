from datetime import datetime
import calendar
from decimal import Decimal
import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.template import loader, Context

from kecupuapp_base.shortcuts import render_response
from kecupuapp_base.decorators import has_role
from kecupuapp_base.forms import process_form
from kecupuapp_base import log

from cari.forms import DateSearchForm

from xpos import models as pos_models
from xpos.models import Payment, OrderItem, Order
from xpos.forms import PaymentForm, OrderItemForm, OrderConfirmForm, OrderForm, OrderCancelForm
from xpos.utils import render_pdf
from xpos.views.pdf import draw_receipt, draw_invoice

from jazzpos.models import Customer, Store, StoreSettings

from gfbv import list_detail

@has_role('staff')
def add_order(request, customer_id):
    customer_model = pos_models.get_class(settings.XPOS_CUSTOMER_MODEL)
    customer = get_object_or_404(customer_model, pk=customer_id)
    order = pos_models.Order(
        customer=customer
    )
    order.save()
    return redirect('/customer/%s/orders/' % customer_id)

@login_required
@has_role('staff')
def list_orders(request, user_id=None):
    if user_id:
        customer = get_object_or_404(Customer, pk=user_id)
    else:
        customer = None
    ctx = {}
    if user_id:
        queryset = pos_models.Order.objects.filter(
            customer__id=user_id
        )
    else:
        queryset=pos_models.Order.objects.all()
    queryset = queryset.filter(store=request.store)
    queryset = queryset.order_by('-created')

    initial = {
        'order_type': customer.customer_type.name,
        'customer': customer,
    }
    ctx['form'] = process_form(request, OrderForm, initial=initial)
    ctx['customer_id'] = int(user_id)
    ctx['customer'] = customer
    ctx['pos_models'] = pos_models

    return list_detail.object_list(
        request,
        queryset=queryset,
        template_object_name='order',
        extra_context=ctx,
    )

@login_required
@has_role('staff')
def show_order(request, order_id):
    order = get_object_or_404(pos_models.Order, pk=order_id)
    payments = Payment.objects.filter(order=order_id)
    initial = {
        'order_id': order_id,
    }
    response_dict = {
        "order_item_form": process_form(request, OrderItemForm, initial=initial),
        "order": order,
        "customer": order.customer,
        "payments": payments,
        "payment_form": process_form(request, PaymentForm, initial=initial),
        "confirm_form": process_form(request, OrderConfirmForm, initial=initial),
        "cancel_form": process_form(request, OrderCancelForm, initial=initial),
    }

    return render_response(
        request,
        'xpos/order_detail.html',
        response_dict
    )

@has_role('staff')
def list_payments(request, order_id):
    ctx = {}
    order = get_object_or_404(pos_models.Order, pk=order_id)
    payments = Payment.objects.filter(order=order_id)
    initial = {
        'order_id': order_id,
    }

    ctx['payments'] = payments
    ctx['order'] = order
    ctx['customer'] = order.customer
    ctx['payment_form'] = process_form(request, PaymentForm, initial=initial)
    return render_response(
        request,
        'xpos/payment_list.html',
        ctx
    )

@has_role('staff')
@require_POST
def add_order_item(request, order_id):
    order = get_object_or_404(pos_models.Order, pk=order_id)
    form = OrderItemForm(request.POST)
    if form.is_valid():
        form.instance.order_id = order_id
        form.save()
    return redirect(reverse(show_order, args=(order_id,)))

@login_required
@has_role('staff')
def print_order(request, order_id):
    order = get_object_or_404(pos_models.Order, pk=order_id)
    payments = Payment.objects.filter(order__customer__id = order.customer.id)
    response_dict = {
        "order": order,
        "payments": payments,
    }

    return render_pdf(
        request,
        'pos/order_print.html',
        response_dict
    ) 

@has_role('staff')
def print_payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)

    ctx = {}
    ctx['order'] = payment.order
    ctx['payment'] = payment
    ctx['print_mode'] = True

    storesettings = StoreSettings.objects.filter(store=request.store)
    for settings in storesettings:
        ctx['storesettings_%s' % settings.name] = settings.value

    response = HttpResponse(content_type="application/pdf")
    #response["Content-Disposition"] = "attachment; filename=receipt.pdf"
    draw_receipt(response, ctx)
    return response

@has_role('staff')
def print_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    ctx = {}
    ctx['order'] = order

    storesettings = StoreSettings.objects.filter(store=request.store)
    for settings in storesettings:
        ctx['storesettings_%s' % settings.name] = settings.value

    response = HttpResponse(content_type="application/pdf")
    #response["Content-Disposition"] = "attachment; filename=invoice.pdf"
    draw_invoice(response, ctx)
    return response

@has_role('staff')
def delete_order(request, order_id=None):
    if not order_id:
        return redirect(reverse(show_order, args=(order_id,)))

    order = get_object_or_404(Order, pk=order_id)
    if order.status != pos_models.ORDER_STATUS_NEW:
        messages.warning(request, "Status order tidak sah")
        return redirect(reverse('pos-orders', args=(order.customer_id,)))

    order.delete()
    return redirect(reverse('pos-orders', args=(order.customer_id,)))

@has_role('staff')
def delete_order_item(request, order_item_id):
    order_item = get_object_or_404(OrderItem, pk=order_item_id)
    order_item.delete()
    order_item.order.save()
    return redirect(reverse(show_order, args=(order_item.order_id,)))

@has_role('staff')
def view_statement(request, customer_id):
    from xpos.utils import sql
    from django.db.models import Sum, F
    from xpos.models import get_previous_order_total, get_previous_payment_total
    from xpos.models import get_all_transactions

    ctx = {}
    customer = get_object_or_404(Customer, pk=customer_id)
    current_date = datetime.now()
    month = request.GET.get('month', current_date.month)
    year = request.GET.get('year', current_date.year)
    first_day, last_day = calendar.monthrange(int(year), int(month))
    fdom = datetime.strptime('%s-%s-%s 00:00:00' % (year, month, 1), '%Y-%m-%d %H:%M:%S')
    ldom = datetime.strptime('%s-%s-%s 23:59:59' % (year, month, last_day), '%Y-%m-%d %H:%M:%S')
    ctx['years'] = range(2013, 2020)
    ctx['selected_year'] = year

    if 'date_start' in request.GET or 'date_end' in request.GET:
        form = DateSearchForm(request.GET)
        if form.is_valid():
            date_start = form.cleaned_data['date_start']
            date_end = form.cleaned_data['date_end']
        else:
            date_start = fdom
            date_end = ldom
    else:
        form = DateSearchForm()
        date_start = fdom
        date_end = ldom

    ctx['search_form'] = form


    previous_order_total = get_previous_order_total(customer, date_start, request.store)
    previous_payment_total = get_previous_payment_total(customer, date_start, request.store)
    current_order_total = get_previous_order_total(customer, date_end, request.store)
    current_payment_total = get_previous_payment_total(customer, date_end, request.store)

    previous_balance = previous_payment_total - previous_order_total
    current_balance = current_payment_total - current_order_total
    ctx['previous_balance'] = previous_balance
    ctx['current_balance'] = current_balance
    ctx['customer'] = customer

    transactions = get_all_transactions(
            request.store,
            customer,
            start_date=date_start,
            end_date=date_end
        )

    if len(transactions) > 0:
        total_credit = sum([txn['amount'] for txn in transactions if txn['type'] == 'credit'])
        total_debit = sum([txn['amount'] for txn in transactions if txn['type'] == 'debit'])
    else:
        total_credit = Decimal('0.00')
        total_debit = Decimal('0.00')

    ctx['transactions'] = transactions
    ctx['total_debit'] = total_debit
    ctx['total_credit'] = total_credit
    # assume total_debit not paid yet, so it's negative
    ctx['current_order_total'] = abs(-(total_debit) + previous_balance)
    
    return render_response(
        request,
        'xpos/account_statement.html',
        ctx
    )

@has_role('staff')
def view_reports(request):
    from xpos.models import get_all_transactions
    from xpos.models import calculate_total_checque_payment
    from xpos.models import calculate_total_cash_payment
    from xpos.models import calculate_total_sale

    if request.GET.get('format', None) == 'csv':
        template = 'xpos/reports.csv'
        output_format = 'csv'
    else:
        template = 'xpos/reports.html'
        output_format = 'html'

    ctx = {}
    current_date = datetime.now()
    day = request.GET.get('day', None)
    month = request.GET.get('month', current_date.month)
    year = request.GET.get('year', current_date.year)
    first_day, last_day = calendar.monthrange(int(year), int(month))

    first_day, last_day = calendar.monthrange(int(year), int(month))
    fdom = datetime.strptime('%s-%s-%s 00:00:00' % (year, month, 1), '%Y-%m-%d %H:%M:%S')
    ldom = datetime.strptime('%s-%s-%s 23:59:59' % (year, month, last_day), '%Y-%m-%d %H:%M:%S')
    if 'date_start' in request.GET or 'date_end' in request.GET:
        form = DateSearchForm(request.GET)
        if form.is_valid():
            date_start = form.cleaned_data['date_start']
            date_end = form.cleaned_data['date_end']
        else:
            date_start = fdom
            date_end = ldom
    else:
        form = DateSearchForm()
        date_start = fdom
        date_end = ldom

    ctx['search_form'] = form

    transactions = get_all_transactions(request.store, start_date=date_start, end_date=date_end)
    if len(transactions) > 0:
        total_cash = calculate_total_cash_payment(transactions)
        total_cheque = calculate_total_checque_payment(transactions)
        total_sale = calculate_total_sale(transactions)
    else:
        total_cash = Decimal('0.00')
        total_cheque = Decimal('0.00')
        total_sale = Decimal('0.00')

    ctx['transactions'] = transactions
    ctx['total_sale'] = total_sale
    ctx['total_cash'] = total_cash
    ctx['total_cheque'] = total_cheque
    ctx['total_payment'] = total_cash + total_cheque
    ctx['report_month'] = month
    ctx['report_year'] = year

    if output_format == 'csv':
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=jazzpos.csv'
        writer = csv.writer(response)
        writer.writerow(['Tarikh', 'Transaksi', 'Belian', 'Bayaran Tunai', 'Bayaran Cek'])
        for transaction in transactions:
            csv_row = []
            csv_row.append(transaction['date'].strftime('%d-%m-%Y'))
            csv_row.append(transaction['description'])
            if transaction['type'] == 'debit':
                csv_row.append(transaction['amount'])
            else:
                csv_row.append('')
            if transaction.get('method', None) == 'TUNAI':
                csv_row.append(transaction['amount'])
            else:
                csv_row.append('')
            if transaction.get('method', None) == 'CEK':
                csv_row.append(transaction['amount'])
            else:
                csv_row.append('')

            writer.writerow(csv_row)
        return response

    return render_response(
        request,
        'xpos/reports.html',
        ctx
    )
