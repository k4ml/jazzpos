from django.conf.urls.defaults import *

import xpos.autocomplete_settings
import xpos.views.main as views_main
import xpos.views.main2 as views_main2
import xpos.views.item as views_item
import xpos.apis.views as views_api

urlpatterns = patterns('',
    url(r'^$', views_main.list_orders, name='pos-index'),
    url(r'^orders/customer/(\d+)/$', views_main.list_orders, name='pos-orders'),
    url(r'^orders/new/(\d+)/$', views_main.add_order, name='pos-orders-add'),
    url(r'^orders/(\d+)/$', views_main.show_order, name='pos-orders-show'),
    url(r'^orders-edit/(\d+)/$', views_main2.show_order, name='pos-orders-edit'),
    url(r'^orders/(\d+)/delete/$', views_main.delete_order, name='pos-orders-delete'),
    url(r'^orders/(\d+)/add-item/$', views_main.add_order_item, name='pos-orders-add-item'),
    url(r'^orders/item/(\d+)/delete/$', views_main.delete_order_item, name='pos-orders-delete-item'),
    url(r'^orders/(\d+)/print$', views_main.print_order, name='pos-orders-print'),
    url(r'^orders/(\d+)/invoice$', views_main.print_invoice, name='pos-orders-invoice'),
    url(r'^orders/(\d+)/payments/$', views_main.list_payments, name='pos-orders-payments'),
    url(r'^payment/(\d+)/receipt/$', views_main.print_payment_receipt, name='pos-orders-payments-print'),
    url(r'^reports/$', views_main.view_reports, name='pos-reports'),
)

urlpatterns += views_item.ItemCRUDL().as_urlpatterns()

urlpatterns += patterns('',
    url(r'^api/order/(?P<pk>\d+)/$', views_api.OrderView.as_view()),
    url(r'^api/stocks/$', views_api.StockListView.as_view()),
)

urlpatterns += patterns('',
    url(r'^stocks/$', views_item.manage_stock, name='pos-stock'),
)
