import datetime

from django import forms
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib import messages
from django.forms.models import inlineformset_factory

from kecupuapp_base import log
from autocomplete.widgets import AutocompleteWidget

from xpos.models import Payment, OrderItem, Order, Item, Stock, ItemPrice
from xpos.models import ORDER_STATUS_NEW, \
    ORDER_STATUS_CONFIRM, ORDER_STATUS_CANCEL, \
    ORDER_STATUS_COMPLETE, PAYMENT_METHOD_CHOICES

from jazzpos.helpers import get_customertype_for_choices

DATE_INPUT_FORMATS = (
    "%d-%m-%Y",
    "%d-%m-%Y %H:%M:%S",
)

class RequestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(RequestForm, self).__init__(*args, **kwargs)
        for k, field in self.fields.items():
            if 'required' in field.error_messages:
                field.error_messages['required'] = 'Perlu diisi'

class RequestModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(RequestModelForm, self).__init__(*args, **kwargs)

        # set store_id if the instance has this attribute
        if self.instance and hasattr(self.instance, 'store_id'):
            self.instance.store_id = self.request.session['store_id']

class PaymentForm(RequestForm):
    amount = forms.DecimalField(label="Jumlah")
    method = forms.CharField(
        label="Kaedah Pembayaran",
        widget=forms.Select(choices=PAYMENT_METHOD_CHOICES)
    )
    checque_no = forms.CharField(required=False, label="No. Cek")
    notes = forms.CharField(
        required=False,
        label="Catatan",
        widget=forms.Textarea(attrs={'rows': 2})
    )

    def clean(self):
        order_id = self.initial['order_id']
        order = Order.objects.get(pk=order_id)
        if order.status != ORDER_STATUS_CONFIRM:
            raise forms.ValidationError("Order tidak sah")
        
        method = self.cleaned_data.get('method', 'CASH')
        checque_no = self.cleaned_data.get('checque_no', None)
        if method == 'CEK' and not checque_no:
            self._errors['checque_no'] = self.error_class(["Sila masukkan nombor cek"])

        return self.cleaned_data

    def execute(self):
        data = self.cleaned_data
        payment = Payment(
            order_id=self.initial['order_id'],
            method=data['method'],
            amount=data['amount'],
            notes=data['notes'],
            checque_no=data['checque_no'],
            store=self.request.store,
        )
        payment.save()

        if payment.order.total_payment() == payment.order.total:
            payment.order.status = ORDER_STATUS_COMPLETE
            payment.order.save()

class OrderForm(RequestModelForm):

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['transaction_date'].required = False
        self.fields['transaction_date'].input_formats = DATE_INPUT_FORMATS
        self.fields['transaction_date'].label = "Tarikh Transaksi"

        self.fields['payment_due_date'].required = False
        self.fields['payment_due_date'].input_formats = DATE_INPUT_FORMATS
        self.fields['payment_due_date'].label = "Tarikh Bayaran"

    def clean_transaction_date(self):
        data = self.cleaned_data['transaction_date']
        if isinstance(data, datetime.datetime):
            return data
        if data is None:
            return datetime.datetime.now()

    def clean_payment_due_date(self):
        data = self.cleaned_data['payment_due_date']
        if isinstance(data, datetime.datetime):
            return data
        if data is None:
            return datetime.datetime.now()

    class Meta:
        model = Order
        #exclude = ('total', 'total_discount', 'status', 'items',)
        fields = ('order_type', 'transaction_date', 'payment_due_date', 'customer',)
        widgets = {
            'order_type': forms.Select(choices=get_customertype_for_choices()),
            'customer': forms.HiddenInput,
        }

class OrderItemForm(RequestModelForm):
    price = forms.DecimalField(required=False)
    item = forms.ModelChoiceField(queryset=None, widget=AutocompleteWidget('items'))

    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        self.fields['item'].error_messages['required'] = 'Sila pilih Item'
        self.fields['item'].queryset = Item.objects.filter(status=1).only('id', 'name')

    def save(self, commit=True):
        self.instance.order_id = self.initial['order_id']
        return super(OrderItemForm, self).save(commit=commit)

    def clean(self):
        super(OrderItemForm, self).clean()
        data = self.cleaned_data
        order_id = self.initial['order_id']
        order = Order.objects.get(pk=order_id)
        item = data.get('item', None)
        qty = data.get('qty', None)

        # validation already failed on qty
        if qty is None:
            return data

        try:
            order_item = OrderItem.objects.get(order=order, item=item)
        except OrderItem.DoesNotExist:
            order_item = None

        if order_item:
            raise forms.ValidationError("Item sudah dimasukkan")

        item_stock = item.total_stock()
        if item_stock == 0:
            raise forms.ValidationError("Item tiada dalam stok")
        if qty > item_stock:
            raise forms.ValidationError("Stok tidak cukup. Jumlah stok: %d" % item_stock)

        return data

    class Meta:
        model = OrderItem
        exclude = ('order', 'discount', 'total', 'total_discount')

class OrderConfirmForm(RequestForm):
    order_id = forms.IntegerField(widget=forms.HiddenInput)

    def execute(self):
        order_id = self.cleaned_data['order_id']
        order = Order.objects.get(pk=order_id)
        order.status = ORDER_STATUS_CONFIRM
        order.save()

class OrderCancelForm(RequestForm):
    order_id = forms.IntegerField(widget=forms.HiddenInput)

    def execute(self):
        order_id = self.cleaned_data['order_id']
        order = Order.objects.get(pk=order_id)

        if order.total_payment() > 0:
            messages.warning(self.request, "Order paid, cannot cancel")
            return None

        if order.status == ORDER_STATUS_CONFIRM:
            order.status = ORDER_STATUS_CANCEL
            order.save()
        else:
            messages.warning(self.request, "Order status must equal to Confirm")

class ItemUpdateForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ('komisen', 'komisen_ahli', 'discount', 'category',
                   'stock_threshold',)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('created', 'qty', 'notes')
        widgets = {
            'qty': forms.TextInput(attrs={'size': 3}),
            'notes': forms.TextInput(attrs={'size': 50}),
        }

    class Media:
        css = {
            'all': ('css/xpos.css',)
        }

    created = forms.DateTimeField(required=False, label='Tarikh (Kosongkan utk tarikh semasa)')

    def clean_created(self):
        data = self.cleaned_data['created']
        if data is None:
            data = datetime.datetime.now()
        return data

ItemStockFormSetBase = inlineformset_factory(Item, Stock, form=StockForm)
ItemPriceFormSet = inlineformset_factory(Item, ItemPrice, fk_name='item')

class ItemStockFormSet(ItemStockFormSetBase):
    def clean(self):
        if any(self.errors):
            return

        total_to_delete = 0
        for data in self.cleaned_data:
            if data.get('id', None) is not None:
                if data['qty'] != data['id'].qty:
                    raise forms.ValidationError('Edit tidak dibenarkan utk stok sedia ada. Masukkan stok baru dengan nilai negatif untuk pembetulan.')
            if data.get('DELETE', False):
                total_to_delete += data['qty']

        item = self.instance
        stock_in_hand = item.total_stock()

        if (total_to_delete > 0 and total_to_delete > stock_in_hand):
            raise forms.ValidationError('Jumlah stok kurang daripada jumlah stok keluar, padam tidak dibenarkan')

        return self.cleaned_data
