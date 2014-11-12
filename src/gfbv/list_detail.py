"""
Temporary wrapper to the deprecated function based generic views.
"""
from django.views.generic import ListView, DetailView

def object_list(request, queryset, paginate_by=None, page=None,
        allow_empty=True, template_name=None, template_loader=None,
        extra_context=None, context_processors=None, template_object_name='object',
        mimetype=None):
    queryset_ = queryset
    template_name_ = template_name

    class ViewWrapper(ListView):
        queryset = queryset_ 
        template_name = template_name_
        context_object_name = '%s_list' % template_object_name

        def get_context_data(self, **kwargs):
            context = super(ViewWrapper, self).get_context_data(**kwargs)
            if extra_context is not None:
                context = dict(context.items() + extra_context.items())

            return context
         
    view_func = ViewWrapper.as_view()
    return view_func(request)

def object_detail(request, queryset, object_id=None, slug=None,
        slug_field='slug', template_name=None, template_name_field=None,
        template_loader=None, extra_context=None,
        context_processors=None, template_object_name='object',
        mimetype=None):
    # avoid reference before assignment error
    # we really need nonlocal !!!
    queryset_ = queryset
    template_name_ = template_name
    slug_field_ = slug_field

    class ViewWrapper(DetailView):
        queryset = queryset_ 
        template_name = template_name_
        slug_field = slug_field_
        context_object_name = template_object_name

    view_func = ViewWrapper.as_view()
    kwargs = {
        'pk': object_id,
    }
    if slug is not None:
        kwargs[slug_field] = slug

    return view_func(request, **kwargs)
