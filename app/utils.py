from datetime import date
import base64
import calendar
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils import timezone
from .models import Bitacora, Paciente

PREFIJO_CIFRADO = 'fernet$'


def registrar_bitacora(usuario, accion, detalle='', ip=None, rol=''):
    Bitacora.objects.create(
        usuario=str(usuario),
        rol=rol or '',
        accion=accion,
        detalle=detalle[:1000],
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
    """IP del cliente. X-Forwarded-For solo se usa si hay proxies de confianza (NUM_PROXIES)."""
    proxies = settings.REST_FRAMEWORK.get('NUM_PROXIES') or 0
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if proxies and xff:
        direcciones = [d.strip() for d in xff.split(',')]
        return direcciones[-min(proxies, len(direcciones))]
    return request.META.get('REMOTE_ADDR')


def contiene_html(texto):
    return isinstance(texto, str) and ('<' in texto or '>' in texto)


def _fernet():
    clave = hashlib.sha256(('clave-referencia:' + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(clave))


def cifrar_referencia(texto):
    if not texto:
        return ''
    return PREFIJO_CIFRADO + _fernet().encrypt(texto.encode()).decode()


def descifrar_referencia(valor):
    """Devuelve '' si el valor se cifró con otra SECRET_KEY."""
    if not valor or not valor.startswith(PREFIJO_CIFRADO):
        return valor or ''
    try:
        return _fernet().decrypt(valor[len(PREFIJO_CIFRADO):].encode()).decode()
    except InvalidToken:
        return ''
