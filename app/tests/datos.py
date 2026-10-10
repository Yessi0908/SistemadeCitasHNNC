"""Datos de prueba compartidos por todas las pruebas unitarias."""
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient

from app.models import Medico, Paciente, Rol

Usuario = get_user_model()

CLAVE_PRUEBA = 'Hnncj#Prueba2026'

USUARIOS_PRUEBA = [
    ('t_admin', Rol.ADMIN),
    ('t_registros', Rol.REGISTROS),
    ('t_archivo', Rol.ARCHIVO),
    ('t_estadistica', Rol.ESTADISTICA),
    ('t_juridico', Rol.JURIDICO),
]

PACIENTE_VALIDO = {
    'primer_apellido': 'López',
    'segundo_apellido': 'García',
    'primer_nombre': 'María',
    'segundo_nombre': 'José',
    'dpi': '2547 89632 0101',
    'direccion': 'Barrio La Esperanza, Jalapa',
    'telefono': '7922-1100',
    'fecha_nacimiento': '1990-05-15',
    'sexo': 'F',
    'estado_civil': 'Casado(a)',
    'especialidad': 'Medicina Interna (MI)',
    'estado_paciente': 'Primera vez',
}

ESP_GENERAL = 'Medicina General (MG)'
ESP_TARDE = 'Psicología Tarde (PST)'
ESP_VAS = 'Violencia y Abuso Sexual (VAS)'

CARGAS_XSS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(document.cookie)>',
    '"><svg onload=alert(1)>',
]

MANANA = date.today() + timedelta(days=1)
AYER = date.today() - timedelta(days=1)


def crear_usuario(username, rol, password=CLAVE_PRUEBA, **extra):
    user = Usuario(username=username, rol=rol, **extra)
    if rol == Rol.ADMIN:
        user.is_staff = True
        user.is_superuser = True
    user.set_password(password)
    user.save()
    return user


def crear_paciente(dpi='1000000000101', nombre='Juan', apellido='Pérez', **extra):
    from app.utils import generar_numero_expediente
    return Paciente.objects.create(
        primer_nombre=nombre, primer_apellido=apellido, dpi=dpi,
        numero_expediente=generar_numero_expediente(), **extra,
    )


def crear_medico(nombre='Dr. Carlos Ruiz', especialidad=ESP_GENERAL, activo=True):
    return Medico.objects.create(nombre=nombre, especialidad=especialidad, activo=activo)


class PruebaAPI(APITestCase):
    """Base: crea un usuario por rol y limpia la caché (límites de intentos)."""

    def setUp(self):
        cache.clear()
        self.usuarios = {rol: crear_usuario(nombre, rol) for nombre, rol in USUARIOS_PRUEBA}

    def cliente(self, rol=None):
        c = APIClient()
        if rol:
            c.force_authenticate(self.usuarios[rol])
        return c


HORA_MANANA = time(9, 0)
HORA_TARDE = time(14, 0)
