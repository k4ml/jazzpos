from django import http
from django.template.loader import get_template
from django.template import RequestContext
import ho.pisa as pisa
import cStringIO as StringIO
import cgi

import os
from os.path import dirname, abspath

MONTHS = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mac',
    4: 'Apr',
    5: 'Mei',
    6: 'Jun',
    7: 'Jul',
    8: 'Ogos',
    9: 'Sep',
    10: 'Okt',
    11: 'Nov',
    12: 'Dis',
}

def _get_css():
    path = abspath(dirname(__file__))
    f = open(os.path.join(path, 'media/pos/css/plain.css'), "r")
    return f.read()

def render_pdf(request, template_src, context_dict):
    template = get_template(template_src)
    context = RequestContext(request, context_dict)
    html  = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(
        StringIO.StringIO(html.encode("UTF-8")), 
        result,
    )
    if not pdf.err:
        return http.HttpResponse(result.getvalue(), \
             mimetype='application/pdf')
    return http.HttpResponse("pdf error! %s" % cgi.escape(html))

def sql(query, param=None):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(query, param)
    description = [x[0] for x in cursor.description]
    for row in cursor.fetchall():
        yield dict(zip(description, row))
