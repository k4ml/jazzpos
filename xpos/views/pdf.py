from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4 # 21 * 29.7 cm
from reportlab.lib.units import cm
from reportlab.lib import colors

def if_blank(value, blank='N/A'):
    return value if value != '' else blank

class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            for count, _code in enumerate(state['_code']):
                state['_code'][count] = state['_code'][count].replace('{NB}', str(num_pages))
            self.__dict__.update(state)
            Canvas.showPage(self)
        Canvas.save(self)

def draw_header(canvas, doc):
    """ Draws the invoice header """
    context = doc.context
    canvas.saveState()
    #canvas.setStrokeColorRGB(0.9, 0.5, 0.2)
    #canvas.setFillColorRGB(0.2, 0.2, 0.2)
    #canvas.setFont('Helvetica', 15)
    canvas.drawString(0.71 * cm, 28 * cm, 'Jazz Store')
    textobject = canvas.beginText()
    textobject.setTextOrigin(0.71 * cm, 27.5 * cm)
    textobject.setFont('Helvetica', 8)

    address = context.get('storesettings_alamat-resit', 'N/A')
    for line in address.split('\n'):
        textobject.textLine(line)
    canvas.drawText(textobject)

    ## Info
    order = context['order']
    customer = order.customer
    payment = context.get('payment', None)

    textobject2 = canvas.beginText()
    textobject2.setTextOrigin(0.71 * cm, textobject.getY())
    textobject2.setFont('Helvetica', 10)
    textobject2.textLine('')
    textobject2.textLine(context['doc_type'])

    if payment is not None:
        textobject2.textLine(u'No Transaksi: #%s' % payment.id)
        textobject2.textLine(u'Tarikh Transaksi: %s' % payment.created.strftime('%d-%m-%Y'))
    else:
        textobject2.textLine(u'No Transaksi: #%s' % order.id)
        textobject2.textLine(u'Tarikh Transaksi: %s' % order.created.strftime('%d-%m-%Y'))

    textobject2.textLine(u'%s (#%s)' % (customer.name, customer.id))
    textobject2.textLine(u'%s' % (if_blank(customer.address)))

    textobject2.textLine('Muka surat: %d daripada {NB}' % (doc.page))
    textobject2.textLine('')
    textobject2.textLine('')
    canvas.drawText(textobject2)

    canvas.restoreState()

def draw_footer(canvas, context):
    """ Draws the invoice footer """
    note = (
        u'Bank Details: Street address, Town, County, POSTCODE',
        u'Sort Code: 00-00-00 Account No: 00000000 (Quote invoice number).',
        u'Please pay via bank transfer or cheque. All payments should be made in CURRENCY.',
        u'Make cheques payable to Company Name Ltd.',
    )
    textobject = canvas.beginText(1 * cm, -27 * cm)
    for line in note:
        textobject.textLine(line)
    canvas.drawText(textobject)

def draw_order_items(canvas, order_items):
    data = [[u'Item', u'Kuantiti', u'Harga (RM)', u'Jumlah (RM)'], ]
    for item in order_items:
        data.append([
            item.item.name,
            item.qty,
            '%.2f' % item.item.price_sale,
            '%.2f' % item.total
        ])
    data.append(['Jumlah Keseluruhan: RM%.2f' % item.order.total, '', '', ''])
    table = Table(data, colWidths=[11 * cm, 2 * cm, 3 * cm, 3 * cm], hAlign='LEFT', repeatRows=1)
    table.setStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), (0.2, 0.2, 0.2)),
        #('GRID', (0, 0), (-1, -2), 1, (0.7, 0.7, 0.7)),
        #('GRID', (-2, -1), (-1, -1), 1, (0.7, 0.7, 0.7)),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'), # price, total
        #('BACKGROUND', (2, 0), (-1, -1), colors.yellow), # price, total
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), # qty
        #('BACKGROUND', (0, 0), (0, -1), colors.yellow), # item
        ('LEFTPADDING', (0, 0), (0, -1), 0), # item
        #('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
    ])
    return table
    tw, th, = table.wrapOn(canvas, 15 * cm, 19 * cm)
    table.drawOn(canvas, 1 * cm, -4 * cm - th)
    return tw, th

def draw_receipt(response, context):
    doc = SimpleDocTemplate(response, topMargin=5.6*cm, leftMargin=0.5*cm)
    context['doc_type'] = 'Resit'
    doc.context = context
    styles = getSampleStyleSheet()
    P = lambda s: Paragraph(s, styles['Normal'])
    stories = []

    payment = context['payment']
    orderitem_list = payment.order.orderitem_set.all()
    stories.append(draw_order_items(doc, orderitem_list))
    stories.append(P('Bayaran: RM%.2f - Terima Kasih.' % payment.amount))
    stories.append(Spacer(1, 1*cm))
    stories.append(P('Tandatangan petugas'))
    stories.append(Spacer(1, 0.5*cm))
    stories.append(HRFlowable(width='22%', hAlign='LEFT', color=colors.black))
    doc.build(stories, onFirstPage=draw_header, onLaterPages=draw_header, canvasmaker=NumberedCanvas)

def draw_invoice(response, context):
    order = context['order']
    customer = order.customer

    doc = SimpleDocTemplate(response, topMargin=5.6*cm, leftMargin=0.5*cm)
    context['doc_type'] = 'Invois'
    doc.context = context
    styles = getSampleStyleSheet()
    P = lambda s: Paragraph(s, styles['Normal'])
    stories = []

    stories.append(draw_order_items(doc, order.orderitem_set.all()))
    stories.append(Spacer(1, 1*cm))
    stories.append(P('Tandatangan petugas'))
    stories.append(Spacer(1, 0.5*cm))
    stories.append(HRFlowable(width='22%', hAlign='LEFT', color=colors.black))
    doc.build(stories, onFirstPage=draw_header, onLaterPages=draw_header, canvasmaker=NumberedCanvas)
