import time
import datetime

from django.db import transaction
from django.utils.decorators import method_decorator

from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from xpos.models import Order, Item
from xpos.apis.serializers import OrderSerializer
from xpos.forms import OrderItemForm, StockForm

class OrderView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    model = Order
    serializer_class = OrderSerializer

    def get(self, request, pk):
        resp_dict = {}
        order = get_object_or_404(Order, pk=pk)
        qs = Item.objects.filter(status=Item.ITEM_STATUS_ACTIVE).select_related()
        order_items = {}
        for order_item in order.orderitem_set.all():
            if order_item.item.id not in order_items:
                order_items[order_item.item.id] = {}
            order_items[order_item.item.id]['selected'] = True
            order_items[order_item.item.id]['qty'] = order_item.qty
            order_items[order_item.item.id]['total'] = order_item.total
            order_items[order_item.item.id]['name'] = order_item.item.name
            order_items[order_item.item.id]['id'] = order_item.item.pk
            order_items[order_item.item.id]['price'] = order_item.price

        resp_dict['id'] = order.pk
        resp_dict['total'] = order.total
        resp_dict['items'] = []
        for item in qs:
            if item.id in order_items:
                resp_dict['items'].append(order_items[item.id])
            else:
                resp_dict['items'].append({
                    'id': item.id,
                    'name': item.name,
                    'selected': False,
                    'price': item.get_price(order.order_type),
                    'qty': 1,
                    'total': 0
                })
        return Response(resp_dict)

    def post(self, request, pk):
        resp = []
        order = get_object_or_404(Order, pk=pk, status=Order.STATUS_NEW)
        for order_item in order.orderitem_set.all():
            order_item.delete()
        order.total = 0
        order.save()

        data = request.DATA
        order_items = data['items']
        initial = {'order_id': order.id}
        for order_item in order_items:
            if order_item['selected'] == False:
                continue
            item = Item.objects.get(pk=order_item['id'])
            order_item['item'] = item.pk
            form = OrderItemForm(order_item, request=request, initial=initial)
            if form.is_valid():
                form.save()
                resp.append('%s saved' % item.name)
            else:
                resp.append('%s %s' % (item.name, form.errors))

        return Response(resp)

class StockListView(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {}
        items = []
        data['current_total'] = 0
        for item in Item.objects.all().select_related():
            item = {
                'id': item.id,
                'name': item.name,
                'price': item.price_cost,
                'qty': 0,
                'total': 0,
                'selected': False,
                'stock': item.total_stock(),
            }
            item['current_total'] = item['stock'] * item['price']
            data['current_total'] += item['current_total']
            items.append(item)

        data['items'] = items
        return Response(data)

    @method_decorator(transaction.commit_manually)
    def post(self, request):
        resp_ok = []
        resp_fail = []
        commit = True
        for item_data in request.DATA:
            if item_data['selected'] == False:
                continue

            item = get_object_or_404(Item, pk=item_data['id'])
            form = StockForm(item_data)
            if form.is_valid():
                form.instance.item = item
                form.save()
            else:
                resp_fail.append('%s - %s' % (item.name, form.errors))
                commit = False

            resp_ok.append('%s saved' % item.name)

        if commit:
            transaction.commit()
            resp = resp_ok
        else:
            transaction.rollback()
            resp = resp_fail

        return Response(resp)
