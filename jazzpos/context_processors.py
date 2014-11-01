
from django.db.models import Count

from jazzpos.models import (
    Store,
    Customer,
    Patient
)

def all(request):
    ctx = {}
    store_id = request.session.get('store_id', None)
    if store_id is None:
        return ctx

    ctx['current_store'] = Store.objects.get(pk=store_id)
    ctx['attached_stores'] = request.user.get_profile().store.all()
    
    if len(ctx['attached_stores']) > 1:
        ctx['has_many_stores'] = True
    else:
        ctx['has_many_stores'] = False

    stats = {}
    stats['total_customers'] = Customer.objects.all().count()
    stats['patients_by_level'] = Patient.objects.values('outer_level') \
                                 .annotate(Count('outer_level')) \
                                 .order_by('-outer_level')
    ctx['stats'] = stats

    return ctx
