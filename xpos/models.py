from decimal import Decimal
from datetime import datetime

from django.db import models
from django.db.models import signals as pos_model_signals, \
    Sum
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.functional import lazy

from jazzpos.helpers import get_customertype_for_choices
from jazzpos.models import CustomerType

#from kecupu.pos.exceptions import NullTotalException

# Create your models here.

ORDER_STATUS_NEW = 0
ORDER_STATUS_CONFIRM = 1
ORDER_STATUS_CANCEL = 2
ORDER_STATUS_COMPLETE = 3

ORDER_STATUS_CHOICES = (
    (ORDER_STATUS_NEW, 'Baru'),
    (ORDER_STATUS_CONFIRM, 'Sah'),
    (ORDER_STATUS_CANCEL, 'Batal'),
    (ORDER_STATUS_COMPLETE, 'Selesai'),
)

PAYMENT_METHOD_CHOICES = (
    ('TUNAI', 'TUNAI'),
    ('CEK', 'CEK'),
    ('KOMISEN', 'KOMISEN'),
)

def get_customertype_for_choices():
    outer = []
    ctypes = CustomerType.objects.all()
    for ctype in ctypes:
        inner = (ctype.name, ctype.description)
        outer.append(inner)
    return outer

Model = models.Model

class Item(Model):
    ITEM_STATUS_ACTIVE = 1
    ITEM_STATUS_INACTIVE = 0
    ITEM_STATUS_CHOICES = (
        (ITEM_STATUS_ACTIVE, 'Aktif'),
        (ITEM_STATUS_INACTIVE, 'Tidak Aktif'),
    )

    name = models.CharField(max_length=255, unique=True)
    price_cost = models.DecimalField(max_digits=7, decimal_places=2)
    price_sale = models.DecimalField(max_digits=7, decimal_places=2)
    komisen = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    komisen_ahli = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=7, 
                                   decimal_places=2, 
                                   default='0.00')
    description = models.TextField(blank=True)
    stock_threshold = models.IntegerField(default=10)
    category = models.CharField(max_length=255)
    status = models.IntegerField(default=1, choices=ITEM_STATUS_CHOICES)

    def save(self, *args, **kwargs):
        self.price_cost = str(self.price_cost)
        self.price_sale = str(self.price_sale)
        self.discount = str(self.discount)
        super(Item, self).save(*args, **kwargs) 

    def total_stock(self):
        qs = self.stock_set.aggregate(models.Sum('qty'))
        total = qs['qty__sum'] if qs['qty__sum'] is not None else 0

        qs = self.orderitem_set.aggregate(models.Sum('qty'))
        total_ordered = qs['qty__sum'] if qs['qty__sum'] is not None else 0

        stock_in_hand = total - total_ordered
        return stock_in_hand

    def get_price(self, customertype=None):
        # TODO: Optimize - this will run a query for each item
        try:
            itemprice = ItemPrice.objects.get(item=self, customertype=customertype)
            price = itemprice.price
        except ItemPrice.DoesNotExist:
            price = self.price_sale

        return price

    def __getattr__(self, name):
        if name.startswith('itemprice_'):
            customertype = name.replace('itemprice_', '')
            try:
                price = self.itemprice_set.get(customertype__name=customertype).price
                return price
            except Exception:
                return None
        return super(Item, self).__getattr__(self, name)

    def __unicode__(self):
        return self.name

class Stock(Model):
    qty = models.IntegerField(verbose_name='Kuantiti')
    created = models.DateTimeField()
    item = models.ForeignKey(Item)
    notes = models.TextField(blank=True)

class Order(Model):
    STATUS_NEW = 0
    STATUS_CONFIRM = 1
    STATUS_CANCEL = 2
    STATUS_COMPLETE = 3

    STATUS_CHOICES = (
        (STATUS_NEW, 'Baru'),
        (STATUS_CONFIRM, 'Sah'),
        (STATUS_CANCEL, 'Batal'),
        (STATUS_COMPLETE, 'Selesai'),
    )

    transaction_date = models.DateTimeField(verbose_name='Tarikh Transaksi')
    payment_due_date = models.DateTimeField(verbose_name='Tarikh Bayaran')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    customer = models.ForeignKey(settings.XPOS_CUSTOMER_MODEL)
    items = models.ManyToManyField(Item, through='OrderItem')
    total = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    total_discount = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    status = models.IntegerField(default=0, choices=ORDER_STATUS_CHOICES)
    order_type = models.CharField(max_length=20, verbose_name='Kategori')
    store = models.ForeignKey('jazzpos.Store')

    def save(self, *args, **kwargs):
        orderitems = self.orderitem_set.all()
        if len(orderitems) == 0:
            self.total = '0.00'
        else:
            self.total = reduce((lambda x,y: x+y), [orderitem.total for orderitem in orderitems])
            self.total_discount = reduce(
                (lambda x,y: x+y), 
                [orderitem.total_discount for orderitem in orderitems]
            )
        super(Order, self).save(*args, **kwargs)

    def total_after_discount(self):
        return self.total - self.total_discount

    def total_payment(self):
        qs = self.payment_set.filter(order=self.id)
        qs = qs.aggregate(total_payment=models.Sum('amount'))
        total = qs['total_payment']
        if not total:
            total = Decimal('0.00')

        return total

    def get_order_type_display(self):
        order_types = get_customertype_for_choices()
        for row in order_types:
            order_type, description = row
            if self.order_type == order_type:
                return description
        return self.order_type

    def is_new(self):
        return self.status == ORDER_STATUS_NEW

    def is_confirm(self):
        return self.status == ORDER_STATUS_CONFIRM

    def is_cancel(self):
        return self.status == ORDER_STATUS_CANCEL

    def is_complete(self):
        return self.status == ORDER_STATUS_COMPLETE

class ItemPrice(Model):
    item = models.ForeignKey('xpos.Item') # has to avoid cyclic import
    customertype = models.ForeignKey(CustomerType)
    price = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        unique_together = ('item', 'customertype')

    def __unicode__(self):
        return '%s-%s' % (self.item.name, self.customertype.description)

class OrderItem(Model):
    item = models.ForeignKey(Item)
    order = models.ForeignKey(Order)
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    discount = models.DecimalField(max_digits=7, 
                                   decimal_places=2, 
                                   default=Decimal('0.00'))
    total = models.DecimalField(max_digits=7, decimal_places=2)
    total_discount = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        unique_together = ('item', 'order')

    def get_price(self):
        if self.price is not None:
            return self.price

        try:
            itemprice = ItemPrice.objects.get(item=self.item, customertype=self.order.order_type)
            price = itemprice.price
        except ItemPrice.DoesNotExist:
            price = self.item.price_sale

        return price

    def save(self, *args, **kwargs):
        price = self.get_price()
        self.price = price
        self.total = price * int(self.qty)
        self.total_discount = self.discount * int(self.qty)

        if self.total == 0: self.total = Decimal('0.00')
        if self.total_discount == 0: self.total_discount = Decimal('0.00')
        if self.discount == 0: self.discount = Decimal('0.00')
        super(OrderItem, self).save(*args, **kwargs)

    def total_after_discount(self):
        return self.total - self.total_discount

class Payment(Model):
    order = models.ForeignKey(Order)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    checque_no = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    store = models.ForeignKey('jazzpos.Store')

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = datetime.now()
        if self.modified is None:
            self.modified = datetime.now()
        super(Payment, self).save(*args, **kwargs)

def update_order_total(sender, **kwargs):
    order_item = kwargs['instance']
    order = order_item.order
    order.total = order.orderitem_set.aggregate(Sum('total'))['total__sum']
    order.save()

pos_model_signals.post_save.connect(update_order_total, sender=OrderItem)

def add_payment(order, data):
    payment = Payment(
        order = order,
        method = 'cash',
        amount = data['amount'],
        notes = data['notes']
    )
    payment.save()

def get_class(django_path):
    from django.utils.importlib import import_module
    app, model_name = django_path.split('.')
    models_module = import_module('%s.models' % (app))
    return getattr(models_module, model_name)

def get_previous_order_total(customer, current_date, store=None):
    qs = Order.objects.filter(customer=customer)
    qs = qs.filter(transaction_date__lt=current_date)
    qs = qs.exclude(status=ORDER_STATUS_CANCEL)
    qs = qs.exclude(status=ORDER_STATUS_NEW)

    if store:
        qs = qs.filter(store=store)

    previous_order_total = qs.aggregate(total=Sum('total'))['total']
    if previous_order_total:
        return previous_order_total
    return Decimal('0.00')

def get_previous_payment_total(customer, current_date, store=None):
    qs = Payment.objects.filter(order__customer=customer)
    qs = qs.filter(created__lt=current_date)

    if store:
        qs = qs.filter(store=store)

    previous_payment_total = qs.aggregate(total=Sum('amount'))['total']
    if previous_payment_total:
        return previous_payment_total
    return Decimal('0.00')

def calculate_total_sale(transactions):
    total = 0
    for transaction in transactions:
        if transaction['type'] == 'debit':
            total += transaction['amount']
    return total

def calculate_total_cash_payment(transactions):
    total = 0
    for transaction in transactions:
        if transaction['type'] == 'credit' and transaction['method'] == 'TUNAI':
            total += transaction['amount']
    return total

def calculate_total_checque_payment(transactions):
    total = 0
    for transaction in transactions:
        if transaction['type'] == 'credit' and transaction['method'] == 'CEK':
            total += transaction['amount']
    return total

def get_all_transactions(store, customer=None, start_date=None, end_date=None):
    qs = Order.objects.filter(store=store)

    if customer:
        qs = qs.filter(customer=customer)
    if start_date and end_date:
        qs = qs.filter(transaction_date__gte=start_date, transaction_date__lte=end_date)

    qs = qs.exclude(status=ORDER_STATUS_CANCEL)
    qs = qs.exclude(status=ORDER_STATUS_NEW)

    transactions = []
    for order in qs:
        txn = {}
        txn['item'] = order
        txn['date'] = order.transaction_date
        item_lists = [order_item.name for order_item in order.items.all()]
        txn['description'] = "Order #%d - %s" % (order.id, " ".join(item_lists))
        txn['amount'] = order.total
        txn['type'] = 'debit'
        transactions.append(txn)

    qs = Payment.objects.filter(order__store=store)
    if customer:
        qs = qs.filter(order__customer=customer)
    if start_date and end_date:
        qs = qs.filter(created__gte=start_date, created__lte=end_date)

    for payment in qs:
        txn = {}
        txn['item'] = payment
        txn['date'] = payment.created
        txn['description'] = "Bayaran untuk Order #%d" % (payment.order.id)
        txn['amount'] = payment.amount
        txn['type'] = 'credit'
        txn['method'] = payment.method
        transactions.append(txn)
    transactions.sort(key=lambda item: item['date'])
    return transactions
