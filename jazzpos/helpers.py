
def get_customertype_for_choices():
    from jazzpos.models import CustomerType
    outer = []
    ctypes = CustomerType.objects.filter(status=CustomerType.STATUS_ACTIVE)
    for ctype in ctypes:
        inner = (ctype.name, ctype.description)
        outer.append(inner)
    return outer
