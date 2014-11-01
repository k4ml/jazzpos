
"""
User created in jazzpos/fixtures/initial_data.json.
"""

import datetime

from django.db.models import Sum
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django_webtest import WebTest

from jazzpos.models import (
    Customer,
    Store
)
from xpos.models import Order, Item, Stock, ORDER_STATUS_CONFIRM

class TestStockFunctional(WebTest):
    INITIAL_STOCK = 2

    def setUp(self):
        self.item = Item.objects.create(name='Jus Harmoni 2',
                                        price_sale='50.00', price_cost='30')
        Stock.objects.create(item=self.item, qty=self.INITIAL_STOCK, created=datetime.datetime.now())

    def tearDown(self):
        self.renew_app()

    def get_logged_in_user(self, username='admin', password='abc123'):
        return User.objects.get(username=username)

    def get_dashboard(self, username='admin', password='abc123'):
        response = self.app.get('/', auto_follow=True)

        if 'Login as %s' % username not in response:
            form = response.form
            form['username'] = 'admin'
            form['password'] = 'abc123'

            response = form.submit().follow()

        return response

    def get_attached_store(self):
        store_id = self.app.session['store_id']
        return Store.objects.get(id=store_id)

    def _add_customer(self, **kwargs):
        dashboard = self.get_dashboard()
        list_customer_page = dashboard.click('Senarai Pelanggan', index=0)
        add_customer_page = list_customer_page.click('Tambah pelanggan')
        form = add_customer_page.forms['jazzpos-views-add_customer']

        for key, value in kwargs.items():
            form[key] = value

        response = form.submit().follow()
        return response

    def _add_order(self):
        self._add_customer(name='kamal')
        customer = Customer.objects.get(name='kamal')
        order_url = reverse('pos-orders', args=(customer.id,))

        order_count = Order.objects.count()
        assert order_count == 0, order_count
        response = self.app.get(order_url, auto_follow=True, user='admin')
        assert response.status_code == 200, response.status_code
        response = response.forms['pos-orders-new'].submit().follow()
        order_count = Order.objects.count()
        assert order_count == 1, order_count
        response = response.click('Lihat')

        form = response.forms['pos-orders-item-new']
        form['item'] = self.item.pk
        form['qty'] = 1
        response = form.submit().follow()

        response = response.forms['pos-orders-confirm'].submit().follow()
        order = response.context['order']
        assert order.status == ORDER_STATUS_CONFIRM, (order.status, ORDER_STATUS_CONFIRM)

    def test_add_stock(self):
        response = self.app.get('/pos/item', auto_follow=True, user='admin')
        response = response.click(self.item.name)
        form = response.forms['smartmin_form']

        form['stock_set-2-qty'] = 1
        response = form.submit().follow()
        response = response.click(self.item.name)
        item = response.context['item']
        stock_count = item.stock_set.aggregate(Sum('qty'))['qty__sum']
        assert stock_count == 3, stock_count

    def test_delete_stock_with_order(self):
        response = self.app.get('/pos/item', auto_follow=True, user='admin')
        response = response.click(self.item.name)
        form = response.forms['smartmin_form']

        self._add_order()
        form = response.forms['smartmin_form']
        form['stock_set-0-DELETE'] = True
        response = form.submit().follow()

        item = response.context['item']
        assert 'Jumlah stok kurang daripada jumlah stok keluar, padam tidak dibenarkan' in response.content
        stock_count = item.stock_set.aggregate(Sum('qty'))['qty__sum']
        assert stock_count == self.INITIAL_STOCK, stock_count

    def test_edit_stock_negative_qty(self):
        response = self.app.get('/pos/item', auto_follow=True, user='admin')
        response = response.click(self.item.name)
        form = response.forms['smartmin_form']

        form['stock_set-0-qty'] = -1
        response = form.submit().follow()
        item = response.context['item']
        stock_count = item.stock_set.aggregate(Sum('qty'))['qty__sum']
        assert stock_count == self.INITIAL_STOCK, stock_count

    def test_add_stock_negative_qty(self):
        response = self.app.get('/pos/item', auto_follow=True, user='admin')
        response = response.click(self.item.name)
        form = response.forms['smartmin_form']

        form['stock_set-2-qty'] = -1
        response = form.submit().follow()
        response = response.click(self.item.name)
        item = response.context['item']
        stock_count = item.stock_set.aggregate(Sum('qty'))['qty__sum']
        assert stock_count == self.INITIAL_STOCK - 1, stock_count
