from jazzpos.models import Store

class StoreMiddleware(object):
    """
    Attach store_id to request.session
    """
    def process_request(self, request):
        # assume request.session exists so this must be placed
        # after SessionMiddleware.
        if not request.user.is_authenticated():
            return None

        try:
            store_id = request.session['store_id']
        except KeyError:
            store_id = None

        if store_id:
            request.store = Store.objects.get(pk=store_id)
            return None

        stores = request.user.profile.store.all()
        if len(stores) == 0:
            request.session['store_id'] = 1
        else:
            request.session['store_id'] = stores[0].id
        
        request.store = Store.objects.get(pk=request.session['store_id'])

        return None

class SearchMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Use process_view instead of process_request so that urls.py being
        executed first. Autocomplete settings take place in urls.py.
        """
        # avoid failure with autocomplete views
        from jazzpos.views import list_customers
        if request.GET.get('q', None) is not None:
            return list_customers(request)
