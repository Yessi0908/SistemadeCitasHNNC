from datetime import date
import calendar
from django.conf import settings
from django.utils import timezone
from .models import Bitacora, Paciente


def registrar_bitacora(usuario, accion, detalle='', ip=None, rol=''):
    Bitacora.objects.create(
        usuario=str(usuario),
        rol=rol or '',
        accion=accion,
        detalle=detalle[:500],
        ip=ip,
    )


def calcular_edad(fecha_nac):
    if not fecha_nac:
        return 0, 0, 0
    hoy = date.today()
    anios = hoy.year - fecha_nac.year
    meses = hoy.month - fecha_nac.month
    dias = hoy.day - fecha_nac.day
    if dias < 0:
        meses -= 1
        mes_ant = hoy.month - 1 or 12
        anio_ant = hoy.year if hoy.month > 1 else hoy.year - 1
        dias += calendar.monthrange(anio_ant, mes_ant)[1]
    if meses < 0:
        anios -= 1
        meses += 12
    return max(anios, 0), max(meses, 0), max(dias, 0)


def edad_a_texto(anios, meses, dias):
    return f'{anios} años, {meses} meses, {dias} días'


def generar_numero_expediente():
    """Formato: 263-ANIO-0001-00 ... 0001-99, luego 263-ANIO-0002-00."""
    anio = timezone.now().year
    codigo = settings.CODIGO_HOSPITAL
    prefijo = f"{codigo}-{anio}-"

    correlativo = 1
    sufijo = 0
    hay_del_anio = False

    for numero in Paciente.objects.filter(
        numero_expediente__startswith=prefijo
    ).values_list('numero_expediente', flat=True):
        partes = numero.split('-')
        if len(partes) < 4 or int(partes[1]) != anio:
            continue
        hay_del_anio = True
        c, s = int(partes[2]), int(partes[3])
        if c > correlativo or (c == correlativo and s > sufijo):
            correlativo, sufijo = c, s

    if not hay_del_anio:
        return f"{codigo}-{anio}-0001-00"

    if sufijo < 99:
        sufijo += 1
    else:
        correlativo += 1
        sufijo = 0

    return f"{codigo}-{anio}-{correlativo:04d}-{sufijo:02d}"


def usuario_bloqueado(user):
    if user.bloqueado_hasta and user.bloqueado_hasta > timezone.now():
        return True
    return False


def obtener_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
