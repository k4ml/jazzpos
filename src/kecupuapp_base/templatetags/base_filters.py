import pytz

from django import template

register = template.Library()

def pdb_trace(variable):
    import pdb; pdb.set_trace()
    return variable

register.filter('pdb_trace', pdb_trace)

@register.filter(name='lookup')
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''

@register.filter(name='date_myt')
def date_myt(dateobj):
    dateobj = dateobj.replace(tzinfo=pytz.utc)
    return dateobj.astimezone(pytz.timezone('Asia/Kuala_Lumpur'))
