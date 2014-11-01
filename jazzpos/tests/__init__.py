
"""
User created in jazzpos/fixtures/initial_data.json.
"""

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django_webtest import WebTest

from jazzpos.models import (
    Customer,
    Store
)

class TestFunctional(WebTest):
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

    def add_customer(self, **kwargs):
        dashboard = self.get_dashboard()
        list_customer_page = dashboard.click('Senarai Pelanggan', index=0)
        add_customer_page = list_customer_page.click('Tambah pelanggan')
        form = add_customer_page.forms['jazzpos-views-add_customer']

        for key, value in kwargs.items():
            form[key] = value

        response = form.submit().follow()
        return response
    
    def test_login(self):
        """
        Test user redirected to login page if not login yet. Dashboard
        displaying main menu:-
            * Senarai Pelanggan
            * Laporan

        Test current attached store displayed in the Info box.
        """
        response = self.get_dashboard()
        self.assertContains(response, "Senarai Pelanggan")
        self.assertContains(response, "Laporan")

        user = User.objects.get(username='admin')
        for store in user.profile.store.all():
            self.assertContains(response, store.name)

    def test_list_customers(self):
        self.add_customer(name='Test Customer')
        self.add_customer(name='Yusuf Taiyyob')

        response = self.get_dashboard()
        response = response.click('Senarai Pelanggan', index=0)

        self.assertContains(response, "Senarai Pelanggan")
        self.assertContains(response, "Nama")
        self.assertContains(response, "Alamat")
        self.assertContains(response, "Kategori")

        for customer in Customer.objects.all():
            self.assertContains(response, customer.name)

    def test_add_customer_blank(self):
        response = self.get_dashboard().click('Senarai Pelanggan', index=0) \
                                       .click('Tambah pelanggan')

        # default category selected
        self.assertContains(response, 'selected="selected">Biasa</option>')
        # current attached store selected
        self.assertContains(response, 'selected="selected">%s</option>' %
                           self.get_attached_store().name)

        form = response.forms['jazzpos-views-add_customer']
        response = form.submit()
        self.assertContains(response, 'This field is required.')
