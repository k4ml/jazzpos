from django import forms

class HiddenField(forms.CharField):
    widget = forms.HiddenInput

class FormRedirectException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

def process_form(request, form_class, initial=None, redirect_to=None, **kwargs):
    """
    Generic form handler, inspired by alex martelli's answer at stackoverflow.
    http://stackoverflow.com/questions/1148684/

    This however modeled after drupal_get_form function that is to handle both
    creating and handling form submission through the same function. Return
    form object if no submission otherwise execute the processing method and 
    raise FormRedirectException.
    
    Need to enable ``kecupuapp_base.middlewares.FormRedirectMiddleware`` to
    handle the redirect exception.
    """
    kwargs['request'] = request
    if initial is not None:
        kwargs['initial'] = initial

    if hasattr(form_class, '__form_id__'):
        form_id = form_class.__form_id__
    else:
        form_id = form_class.__name__
    form_id_field_name = 'form_id_%s' % form_id

    if request.method == 'POST':
        request_post = request.POST
        submitted = request.POST.get(form_id_field_name, None)
    else:
        request_post = None
        submitted = False

    if submitted != form_id:
        request_post = None

    if redirect_to is None:
        redirect_to = request.path

    form = form_class(request_post, **kwargs)
    form.fields[form_id_field_name] = HiddenField(initial=form_id)

    if form.is_bound and form.is_valid():
        if hasattr(form, 'save'):
            form.save()
            raise FormRedirectException(redirect_to)

        if hasattr(form, 'execute'):
            form.execute()
            raise FormRedirectException(redirect_to)
    
    return form
