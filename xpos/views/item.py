import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect

from xpos.models import Item
from xpos.forms import ItemUpdateForm, ItemStockFormSet, ItemForm, ItemPriceFormSet

from smartmin.views import SmartCRUDL, SmartListView, SmartCreateView, SmartUpdateView

class ItemCRUDL(SmartCRUDL):
    model = Item

    class List(SmartListView):
        default_order = 'id'
        fields = ('name', 'description', 'status', 'price_cost', 'price_sale')

        def lookup_field_link(self, context, field, obj):
            return reverse('xpos.item_update', args=(obj.id,))

        def get_queryset(self, **kwargs):
            queryset = super(ItemCRUDL.List, self).get_queryset(**kwargs)
            return queryset.exclude(status=0)

        def get_context_data(self, **kwargs):
            from jazzpos.models import CustomerType
            context = super(ItemCRUDL.List, self).get_context_data(**kwargs)
            qs = CustomerType.objects.filter(status=CustomerType.STATUS_ACTIVE)
            price_fields = ['itemprice_%s' % c.name for c in qs]
            context['fields'] += tuple(price_fields)
            return context

    class Create(SmartCreateView):
        form_class = ItemUpdateForm

    class Update(SmartUpdateView):
        form_class = ItemUpdateForm
        default_template = 'smartmin/xpos/update.html'

        def get_context_data(self, **kwargs):
            context = super(ItemCRUDL.Update, self).get_context_data(**kwargs)
            initial = {
                'created': datetime.datetime.now(),
            }
            stock_formset = ItemStockFormSet(instance=self.object)
            itemprice_formset = ItemPriceFormSet(instance=self.object)
            context['stock_formset'] = stock_formset
            context['itemprice_formset'] = itemprice_formset
            return context

        def form_valid(self, form):
            if self.request.method == 'POST':
                stock_formset = ItemStockFormSet(self.request.POST, instance=self.object)
                if stock_formset.is_valid():
                    stock_formset.save()
                else:
                    from django.contrib import messages
                    for error in stock_formset.non_form_errors():
                        messages.error(self.request, error)
                    redirect_url = reverse(self.parent.url_name_for_action('update'), args=(self.object.id,))
                    return HttpResponseRedirect(redirect_url)

                itemprice_formset = ItemPriceFormSet(self.request.POST, instance=self.object)
                if itemprice_formset.is_valid():
                    itemprice_formset.save()
                else:
                    # TODO: show messages
                    raise Exception(stock_formset.errors)

            return super(ItemCRUDL.Update, self).form_valid(form)

def manage_stock(request):
    return render(request, 'xpos/stock_edit.html')
