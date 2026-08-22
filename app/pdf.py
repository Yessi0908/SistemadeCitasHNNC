import io
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Flowable,
    KeepInFrame,
)
from django.conf import settings


AZUL = colors.HexColor('#003366')
AZUL_SUAVE = colors.HexColor('#E8EEF4')
NEGRO = colors.black
GRIS = colors.HexColor('#4A4A4A')
GRIS_LINEA = colors.HexColor('#666666')
GRIS_CLARO = colors.HexColor('#F4F4F4')
GRIS_ETIQUETA = colors.HexColor('#333333')
BLANCO = colors.white

# Estilo de tablas con espacio amplio para expediente
ESTILO_TABLA_EXP = [
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BACKGROUND', (0, 0), (0, -1), AZUL),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
    ('TEXTCOLOR', (1, 0), (1, -1), NEGRO),
    ('BACKGROUND', (1, 0), (1, -1), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
]


def _estilos():
    base = getSampleStyleSheet()
    titulo = ParagraphStyle('titulo', parent=base['Heading1'], fontSize=14, textColor=AZUL, alignment=1)
    normal = ParagraphStyle('normal', parent=base['Normal'], fontSize=10, textColor=NEGRO)
    seccion = ParagraphStyle('seccion', parent=base['Heading2'], fontSize=11, textColor=AZUL, spaceBefore=12, spaceAfter=6)
    return titulo, normal, seccion


def _estilos_form():
    """Estilos de formulario hospitalario impreso (etiquetas pequeñas, valores legibles)."""
    return {
        'inst_sm': ParagraphStyle(
            'inst_sm', fontName='Helvetica', fontSize=8, textColor=AZUL,
            alignment=TA_CENTER, leading=10, spaceAfter=1,
        ),
        'inst_md': ParagraphStyle(
            'inst_md', fontName='Helvetica-Bold', fontSize=9, textColor=AZUL,
            alignment=TA_CENTER, leading=11, spaceAfter=1,
        ),
        'inst_lg': ParagraphStyle(
            'inst_lg', fontName='Helvetica-Bold', fontSize=11, textColor=AZUL,
            alignment=TA_CENTER, leading=13, spaceAfter=2,
        ),
        'inst_exp': ParagraphStyle(
            'inst_exp', fontName='Helvetica-Bold', fontSize=10, textColor=NEGRO,
            alignment=TA_CENTER, leading=12, spaceAfter=1,
        ),
        'inst_exp_sub': ParagraphStyle(
            'inst_exp_sub', fontName='Helvetica-Bold', fontSize=9, textColor=NEGRO,
            alignment=TA_CENTER, leading=11, spaceAfter=0,
        ),
        'titulo_caja': ParagraphStyle(
            'titulo_caja', fontName='Helvetica-Bold', fontSize=11, textColor=AZUL,
            alignment=TA_CENTER, leading=13,
        ),
        'lab': ParagraphStyle(
            'lab', fontName='Helvetica', fontSize=7.5, textColor=GRIS_ETIQUETA,
            alignment=TA_LEFT, leading=9, spaceAfter=1,
        ),
        'lab_c': ParagraphStyle(
            'lab_c', fontName='Helvetica', fontSize=7.5, textColor=GRIS_ETIQUETA,
            alignment=TA_CENTER, leading=9, spaceAfter=1,
        ),
        'lab_carnet': ParagraphStyle(
            'lab_carnet', fontName='Helvetica', fontSize=8, textColor=AZUL,
            alignment=TA_LEFT, leading=10, spaceAfter=1,
        ),
        'val': ParagraphStyle(
            'val', fontName='Helvetica-Bold', fontSize=9, textColor=NEGRO,
            alignment=TA_LEFT, leading=11,
        ),
        'val_n': ParagraphStyle(
            'val_n', fontName='Helvetica', fontSize=9, textColor=NEGRO,
            alignment=TA_LEFT, leading=11,
        ),
        'val_c': ParagraphStyle(
            'val_c', fontName='Helvetica-Bold', fontSize=9, textColor=NEGRO,
            alignment=TA_CENTER, leading=11,
        ),
        'exp_num': ParagraphStyle(
            'exp_num', fontName='Helvetica-Bold', fontSize=16, textColor=AZUL,
            alignment=TA_CENTER, leading=20,
        ),
        'hc': ParagraphStyle(
            'hc', fontName='Helvetica-Bold', fontSize=9, textColor=AZUL,
            alignment=TA_CENTER, leading=11, spaceAfter=2,
        ),
        'th': ParagraphStyle(
            'th', fontName='Helvetica-Bold', fontSize=7, textColor=NEGRO,
            alignment=TA_CENTER, leading=9,
        ),
        'td': ParagraphStyle(
            'td', fontName='Helvetica', fontSize=7.5, textColor=NEGRO,
            alignment=TA_CENTER, leading=9,
        ),
        'firma': ParagraphStyle(
            'firma', fontName='Helvetica', fontSize=9, textColor=NEGRO,
            alignment=TA_LEFT, leading=11,
        ),
        'pie_titulo': ParagraphStyle(
            'pie_titulo', fontName='Helvetica-Bold', fontSize=13, textColor=NEGRO,
            alignment=TA_CENTER, leading=15, spaceBefore=0, spaceAfter=0,
        ),
        'pie_sub': ParagraphStyle(
            'pie_sub', fontName='Helvetica', fontSize=8, textColor=GRIS,
            alignment=TA_CENTER, leading=10, spaceBefore=1, spaceAfter=0,
        ),
        'nota': ParagraphStyle(
            'nota', fontName='Helvetica', fontSize=8, textColor=NEGRO,
            alignment=TA_LEFT, leading=10,
        ),
        'secc_diag': ParagraphStyle(
            'secc_diag', fontName='Helvetica-Bold', fontSize=9, textColor=NEGRO,
            alignment=TA_LEFT, leading=11,
        ),
    }


def _xml(texto):
    return (
        str(texto)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def _v(valor):
    return str(valor) if valor not in (None, '') else '—'


def _fecha(valor):
    if valor in (None, ''):
        return '—'
    if hasattr(valor, 'strftime'):
        return valor.strftime('%d/%m/%Y')
    return str(valor)


def _unir(*partes):
    texto = ' '.join(str(p).strip() for p in partes if p not in (None, ''))
    return texto if texto else '—'


def _sexo(paciente):
    if paciente.sexo == 'M':
        return 'Masculino'
    if paciente.sexo == 'F':
        return 'Femenino'
    return '—'


def _p(texto, estilo):
    return Paragraph(_xml(texto), estilo)


def _campo(etiqueta, valor, estilos, centrado=False, bold=True):
    lab = estilos['lab_c'] if centrado else estilos['lab']
    if centrado:
        val_st = estilos['val_c']
    else:
        val_st = estilos['val'] if bold else estilos['val_n']
    return [_p(etiqueta, lab), _p(_v(valor), val_st)]


def _logo_si_existe(ancho=1.2 * inch, alto=1.2 * inch):
    if settings.LOGO_RUTA.exists():
        try:
            return Image(str(settings.LOGO_RUTA), width=ancho, height=alto)
        except Exception:
            pass
    return None


def _logo_secundario(ancho=0.85 * inch, alto=0.85 * inch):
    ruta = getattr(settings, 'LOGO_SIGSA', None)
    if not ruta:
        return None
    path = Path(ruta)
    if not path.exists():
        return None
    try:
        return Image(str(path), width=ancho, height=alto)
    except Exception:
        return None


def _encabezado(elements, titulo_doc):
    titulo_st, _, _ = _estilos()
    logo = _logo_si_existe()
    if logo:
        elements.append(logo)
    elements.append(Paragraph('Hospital Nacional Nicolasa Cruz Jalapa', titulo_st))
    elements.append(Paragraph(titulo_doc, titulo_st))
    elements.append(Spacer(1, 0.25 * inch))


def _tabla_seccion(filas, ancho_etiqueta=170, ancho_valor=340):
    t = Table(filas, colWidths=[ancho_etiqueta, ancho_valor])
    t.setStyle(TableStyle(ESTILO_TABLA_EXP))
    return t


class _ZonaEscritura(Flowable):
    """Zona de diagnóstico/evolución con líneas para escritura manuscrita."""

    def __init__(self, alto, n_lineas=16, anotaciones=None):
        super().__init__()
        self.alto = alto
        self.n_lineas = n_lineas
        self.anotaciones = anotaciones or []
        self._ancho = 500

    def wrap(self, availWidth, availHeight):
        self._ancho = availWidth
        return availWidth, self.alto

    def draw(self):
        canvas = self.canv
        paso = self.alto / float(self.n_lineas)
        canvas.setStrokeColor(GRIS_LINEA)
        canvas.setLineWidth(0.35)
        for i in range(1, self.n_lineas + 1):
            y = self.alto - (i * paso)
            canvas.line(2, y, self._ancho - 2, y)
            if i - 1 < len(self.anotaciones):
                texto = self.anotaciones[i - 1]
                if not texto:
                    continue
                canvas.setFillColor(NEGRO)
                canvas.setFont('Helvetica', 8)
                max_w = self._ancho - 10
                recorte = texto
                while recorte and stringWidth(recorte, 'Helvetica', 8) > max_w:
                    recorte = recorte[:-1]
                if recorte != texto and len(recorte) > 3:
                    recorte = recorte[:-3] + '...'
                canvas.drawString(4, y + 4, recorte)


def pdf_respuesta(buffer, nombre='documento.pdf'):
    from django.http import HttpResponse
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response


def _consultas_paciente(paciente):
    try:
        return list(paciente.consultas.all().order_by('fecha', 'hora'))
    except Exception:
        return []

#Carnet Hospital
def generar_carnet(paciente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=28,
        bottomMargin=28,
        leftMargin=28,
        rightMargin=28,
    )
    st = _estilos_form()
    ancho = letter[0] - 56
    col_izq = 338
    col_der = ancho - col_izq

    consultas = _consultas_paciente(paciente)
    n_filas = 15
    filas = [[
        _p('Fecha de Ingreso', st['th']),
        _p('Fecha de Egreso', st['th']),
        _p('Diagnóstico', st['th']),
        _p('Servicio', st['th']),
    ]]
    for i in range(n_filas):
        if i < len(consultas):
            c = consultas[i]
            filas.append([
                _p(_fecha(c.fecha), st['td']),
                _p('', st['td']),
                _p(c.motivo or getattr(c, 'notas', '') or '', st['td']),
                _p(_v(c.especialidad), st['td']),
            ])
        else:
            filas.append(['', '', '', ''])

    anchos_citas = [72, 72, 112, col_izq - 256]
    tabla_citas = Table(filas, colWidths=anchos_citas, rowHeights=[32] + [34] * n_filas)
    tabla_citas.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_SUAVE),
        ('TEXTCOLOR', (0, 0), (-1, 0), AZUL),
        ('GRID', (0, 0), (-1, -1), 0.45, GRIS_LINEA),
        ('BOX', (0, 0), (-1, -1), 0.8, AZUL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 1), (-1, -1), BLANCO),
    ]))

    firma = Table(
        [[_p('Firma Médico', st['firma']), '']],
        colWidths=[78, col_izq - 86],
    )
    firma.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LINEBELOW', (1, 0), (1, 0), 0.8, NEGRO),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    izquierda = Table(
        [[tabla_citas], [firma]],
        colWidths=[col_izq],
    )
    izquierda.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    logo = _logo_si_existe(0.72 * inch, 0.72 * inch)
    titulo_caja = Table(
        [[_p('TARJETA DE CITAS', st['titulo_caja'])]],
        colWidths=[col_der - 8],
    )
    titulo_caja.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.1, AZUL),
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_SUAVE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    historia = Table(
        [[_p(_v(paciente.numero_expediente), st['exp_num'])]],
        colWidths=[col_der - 8],
    )
    historia.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 0.9, AZUL),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), GRIS_CLARO),
    ]))

    rx_ekg = Table(
        [[
            [_p('RX', st['lab_carnet']), _p(' ', st['val'])],
            [_p('EKG', st['lab_carnet']), _p(' ', st['val'])],
        ]],
        colWidths=[(col_der - 8) / 2.0, (col_der - 8) / 2.0],
    )
    rx_ekg.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.6, GRIS_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    nombres = Table(
        [[
            [_p('Apellidos:', st['lab_carnet']), _p(_unir(paciente.primer_apellido, paciente.segundo_apellido), st['val'])],
            [_p('Nombres:', st['lab_carnet']), _p(_unir(paciente.primer_nombre, paciente.segundo_nombre), st['val'])],
        ]],
        colWidths=[(col_der - 8) * 0.52, (col_der - 8) * 0.48],
    )
    nombres.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.6, GRIS_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 8),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    admision = Table(
        [[
            [_p('Fecha Admisión', st['lab_carnet']), _p(_fecha(paciente.fecha_ingreso), st['val'])],
            [_p('Registro:', st['lab_carnet']), _p('1', st['val'])],
        ]],
        colWidths=[(col_der - 8) * 0.58, (col_der - 8) * 0.42],
    )
    admision.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.6, GRIS_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 8),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    extras = Table(
        [[
            [_p('CUI (CODIGO UNICO DE IDENTIFICACION)', st['lab_carnet']), _p(_v(paciente.dpi), st['val_n'])],
            [_p('Especialidad', st['lab_carnet']), _p(_v(paciente.especialidad), st['val_n'])],
        ]],
        colWidths=[(col_der - 8) * 0.50, (col_der - 8) * 0.50],
    )
    extras.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 8),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    encabezado_der = [
        _p('MINISTERIO DE SALUD PUBLICA Y ASISTENCIA SOCIAL', st['inst_sm']),
        _p('HOSPITAL NACIONAL NICOLASA CRUZ JALAPA', st['inst_lg']),
        Spacer(1, 6),
        titulo_caja,
        Spacer(1, 6),
    ]
    if logo:
        logo_caja = Table([[logo]], colWidths=[col_der - 8])
        logo_caja.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        encabezado_der.append(logo_caja)
        encabezado_der.append(Spacer(1, 4))
    encabezado_der.extend([
        _p('REGISTROS MÉDICOS Y ESTADÍSTICAS', st['inst_sm']),
        Spacer(1, 10),
        _p('HISTORIA CLÍNICA', st['hc']),
        historia,
        Spacer(1, 8),
        rx_ekg,
        Spacer(1, 6),
        nombres,
        Spacer(1, 6),
        admision,
        Spacer(1, 4),
        extras,
    ])

    derecha = Table([[el] for el in encabezado_der], colWidths=[col_der])
    derecha.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    cuerpo = Table([[izquierda, derecha]], colWidths=[col_izq, col_der])
    cuerpo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1.0, AZUL),
        ('LINEAFTER', (0, 0), (0, 0), 0.6, AZUL),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
    ]))

    doc.build([cuerpo])
    return pdf_respuesta(buffer, f'carnet_{paciente.numero_expediente}.pdf')


def _fila_form(celdas, anchos, alto):
    t = Table([celdas], colWidths=anchos, rowHeights=[alto])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
    ]))
    return t

#Hoja de Expediente
def generar_hoja_expediente(paciente, consultas):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=16,
        bottomMargin=12,
        leftMargin=22,
        rightMargin=22,
    )
    st = _estilos_form()
    ancho = letter[0] - 44

    logo_izq = _logo_si_existe(0.82 * inch, 0.82 * inch)
    logo_der = _logo_secundario(0.82 * inch, 0.82 * inch)
    textos_inst = [
        _p('MINISTERIO DE SALUD PUBLICA Y ASISTENCIA SOCIAL', st['inst_exp']),
        _p('HOSPITAL NACIONAL NICOLASA CRUZ JALAPA', st['inst_exp_sub']),
    ]
    centro_inst = Table([[el] for el in textos_inst], colWidths=[ancho - 180])
    centro_inst.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    encabezado = Table(
        [[logo_izq or '', centro_inst, logo_der or '']],
        colWidths=[90, ancho - 180, 90],
        rowHeights=[70],
    )
    encabezado.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
        ('LINEBELOW', (0, 0), (-1, 0), 0.9, NEGRO),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    c1 = (ancho - 128) / 4.0
    fila1 = _fila_form(
        [
            _campo('1er. Apellido', paciente.primer_apellido, st),
            _campo('2do. Apellido', paciente.segundo_apellido, st),
            _campo('1er. Nombre', paciente.primer_nombre, st),
            _campo('2do. Nombre', paciente.segundo_nombre, st),
            _campo('No. Exp. Médico', paciente.numero_expediente, st),
        ],
        [c1, c1, c1, c1, 128],
        28,
    )

    fila2 = _fila_form(
        [
            _campo('Dirección Actual', paciente.direccion, st, bold=False),
            _campo('Teléfono Personal', paciente.telefono, st),
        ],
        [ancho - 150, 150],
        36,
    )

    edad = Table(
        [[
            _campo('Años', paciente.edad_anios, st, centrado=True),
            _campo('Meses', paciente.edad_meses, st, centrado=True),
            _campo('Días', paciente.edad_dias, st, centrado=True),
        ]],
        colWidths=[50, 50, 50],
    )
    edad.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LINEAFTER', (0, 0), (1, 0), 0.3, GRIS_LINEA),
    ]))
    celda_edad = [_p('Edad', st['lab_c']), edad]

    fila3 = _fila_form(
        [
            _campo('Fecha de Nacimiento', _fecha(paciente.fecha_nacimiento), st),
            celda_edad,
            _campo('Lugar de Nacimiento', paciente.lugar_nacimiento, st, bold=False),
            _campo('Sexo', _sexo(paciente), st),
        ],
        [128, 158, ancho - 128 - 158 - 86, 86],
        34,
    )

    fila4 = _fila_form(
        [
            _campo('Estado Civil', paciente.estado_civil, st),
            _campo('Ocupación', paciente.ocupacion, st, bold=False),
            _campo('Nacionalidad', paciente.nacionalidad, st),
            _campo('CUI', paciente.dpi, st),
        ],
        [110, ancho - 110 - 130 - 150, 130, 150],
        28,
    )

    fila5 = _fila_form(
        [
            _campo('Cónyuge', paciente.nombre_conyuge, st, bold=False),
            _campo('Dirección del cónyuge', '', st, bold=False),
            _campo('Teléfono del cónyuge', '', st),
        ],
        [ancho - 280, 160, 120],
        34,
    )

    fila6 = _fila_form(
        [
            _campo('Nombre del padre', paciente.nombre_padre, st, bold=False),
            _campo('Nombre de la madre', paciente.nombre_madre, st, bold=False),
        ],
        [ancho / 2.0, ancho / 2.0],
        32,
    )

    fila7 = _fila_form(
        [
            _campo('En caso de emergencia notificar', paciente.contacto_emergencia_nombre, st, bold=False),
            _campo('Dirección', '', st, bold=False),
            _campo('Teléfono', paciente.contacto_emergencia_telefono, st),
        ],
        [ancho - 280, 160, 120],
        38,
    )

    fila8 = _fila_form(
        [
            _campo('Otras hospitalizaciones', '', st, bold=False),
            _campo('Referido de', '', st, bold=False),
        ],
        [ancho / 2.0, ancho / 2.0],
        26,
    )

    titulo_diag = Table(
        [[_p('Diagnóstico/Evolución', st['secc_diag'])]],
        colWidths=[ancho],
        rowHeights=[16],
    )
    titulo_diag.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), GRIS_CLARO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    lista_consultas = list(consultas) if consultas is not None else []
    anotaciones = []
    for c in lista_consultas[:5]:
        partes = [
            _fecha(getattr(c, 'fecha', None)),
            _v(getattr(c, 'especialidad', '')),
            _v(getattr(c, 'medico', '')),
            (getattr(c, 'motivo', None) or '')[:90] or '—',
        ]
        anotaciones.append('   |   '.join(partes))

    zona = _ZonaEscritura(alto=336, n_lineas=17, anotaciones=anotaciones)
    caja_escritura = Table([[zona]], colWidths=[ancho], rowHeights=[340])
    caja_escritura.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
    ]))

    pie = Table(
        [[
            _campo('Fecha', date.today().strftime('%d/%m/%Y'), st),
            [
                _p('Firma y No. de Clave de Médico Responsable', st['lab']),
                Spacer(1, 14),
                Table(
                    [['']],
                    colWidths=[ancho - 168],
                    rowHeights=[8],
                    style=TableStyle([
                        ('LINEABOVE', (0, 0), (-1, -1), 0.7, NEGRO),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ]),
                ),
            ],
        ]],
        colWidths=[150, ancho - 150],
        rowHeights=[38],
    )
    pie.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('VALIGN', (1, 0), (1, 0), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
    ]))

    formulario = Table(
        [
            [encabezado],
            [fila1],
            [fila2],
            [fila3],
            [fila4],
            [fila5],
            [fila6],
            [fila7],
            [fila8],
            [titulo_diag],
            [caja_escritura],
            [pie],
        ],
        colWidths=[ancho],
        rowHeights=[70, 28, 36, 34, 28, 34, 32, 38, 26, 16, 340, 38],
    )
    formulario.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, NEGRO),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), BLANCO),
    ]))

    pie_docs = [_p('HOJA DE CONSULTA EXTERNA', st['pie_titulo'])]
    registrado = ''
    for c in lista_consultas:
        creado = getattr(c, 'creado_por', '') or ''
        if creado:
            registrado = creado
            break
    if registrado:
        pie_docs.append(_p(f'registrado por: {registrado}', st['pie_sub']))

    alto_pagina = letter[1] - 28
    elements = [KeepInFrame(
        ancho,
        alto_pagina,
        [formulario, Spacer(1, 4)] + pie_docs,
        mode='shrink',
        fakeWidth=False,
    )]

    doc.build(elements)
    return pdf_respuesta(buffer, f'expediente_{paciente.numero_expediente}.pdf')


def generar_constancia_laboral(paciente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    _encabezado(elements, 'Constancia Laboral / Médica')
    _, normal, _ = _estilos()
    texto = (
        f'Por medio de la presente se hace constar que el/la paciente '
        f'<b>{paciente.nombre_completo}</b>, con DPI <b>{paciente.dpi}</b> '
        f'y expediente <b>{paciente.numero_expediente}</b>, '
        f'especialidad <b>{_v(paciente.especialidad)}</b>, '
        f'se encuentra registrado/a en consulta externa del hospital.'
    )
    elements.append(Paragraph(texto, normal))
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(f'Fecha: {date.today().strftime("%d/%m/%Y")}', normal))
    doc.build(elements)
    return pdf_respuesta(buffer, f'constancia_{paciente.numero_expediente}.pdf')


def generar_registro_diario(registro, detalles):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, landscape=True)
    elements = []
    _encabezado(elements, f'Registro Diario de Consulta — {registro.fecha}')
    filas = [['#', 'Expediente', 'Paciente', 'Especialidad']]
    for i, d in enumerate(detalles, 1):
        filas.append([str(i), d.paciente.numero_expediente, d.paciente.nombre_completo, d.especialidad])
    t = Table(filas, colWidths=[30, 120, 280, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    doc.build(elements)
    return pdf_respuesta(buffer, f'registro_diario_{registro.fecha}.pdf')
