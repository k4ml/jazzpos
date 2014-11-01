def base_site(request):
    """
    Inject few template variables that we need in base template.
    """
    from django.conf import settings

    context = {}
    context['STATIC_URL'] = '/static/'
    context['BASE_SIDEBAR'] = 'yui-t2'

    if hasattr(settings, 'STATIC_URL'):
        context['STATIC_URL'] = settings.STATIC_URL

    if not hasattr(settings, 'BASE_SIDEBAR'):
        return context

    if settings.BASE_SIDEBAR == 'left':
        context['BASE_SIDEBAR'] = 'yui-t2'
    if settings.BASE_SIDEBAR == 'right':
        context['BASE_SIDEBAR'] = 'yui-t4'

    return context
