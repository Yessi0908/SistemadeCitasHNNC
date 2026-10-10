from datetime import date, time, timedelta

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone

from app.catalogos import (
    ESPECIALIDADES, ESPECIALIDADES_TARDE, hora_permitida_para_especialidad,
)
from app.models import Bitacora, Rol
from app.utils import (
    calcular_edad, edad_a_texto, generar_numero_expediente, obtener_ip,
    registrar_bitacora, usuario_bloqueado,
)

from .datos import ESP_GENERAL, ESP_TARDE, crear_paciente, crear_usuario


def hace_anios(n):
    hoy = date.today()
    try:
        return hoy.replace(year=hoy.year - n)
    except ValueError:
        return hoy.replace(year=hoy.year - n, day=28)


class CalculoEdadTests(SimpleTestCase):
    def test_sin_fecha_devuelve_ceros(self):
        self.assertEqual(calcular_edad(None), (0, 0, 0))

    def test_cumpleanios_exacto(self):
        self.assertEqual(calcular_edad(hace_anios(30)), (30, 0, 0))

    def test_un_dia_antes_del_cumpleanios(self):
        anios, meses, _ = calcular_edad(hace_anios(30) + timedelta(days=1))
        self.assertEqual(anios, 29)
        self.assertEqual(meses, 11)

    def test_recien_nacido(self):
        self.assertEqual(calcular_edad(date.today()), (0, 0, 0))

    def test_texto_de_edad(self):
        self.assertEqual(edad_a_texto(5, 2, 1), '5 años, 2 meses, 1 días')


class NumeroExpedienteTests(TestCase):
    def setUp(self):
        self.anio = timezone.now().year

    def test_primer_expediente_del_anio(self):
        self.assertEqual(generar_numero_expediente(), f'263-{self.anio}-0001-00')

    def test_incrementa_sufijo(self):
        crear_paciente(dpi='1')
        self.assertEqual(generar_numero_expediente(), f'263-{self.anio}-0001-01')

    def test_despues_de_99_avanza_correlativo(self):
        from app.models import Paciente
        Paciente.objects.create(
            primer_nombre='A', primer_apellido='B', dpi='2', numero_expediente=f'263-{self.anio}-0001-99',
        )
        self.assertEqual(generar_numero_expediente(), f'263-{self.anio}-0002-00')

    def test_ignora_expedientes_de_otros_anios(self):
        from app.models import Paciente
        Paciente.objects.create(
            primer_nombre='A', primer_apellido='B', dpi='3', numero_expediente=f'263-{self.anio - 1}-0050-10',
        )
        self.assertEqual(generar_numero_expediente(), f'263-{self.anio}-0001-00')


class BloqueoYBitacoraTests(TestCase):
    def test_usuario_bloqueado_mientras_no_expira(self):
        u = crear_usuario('b1', Rol.ARCHIVO, bloqueado_hasta=timezone.now() + timedelta(minutes=5))
        self.assertTrue(usuario_bloqueado(u))

    def test_usuario_desbloqueado_al_expirar(self):
        u = crear_usuario('b2', Rol.ARCHIVO, bloqueado_hasta=timezone.now() - timedelta(minutes=1))
        self.assertFalse(usuario_bloqueado(u))

    def test_bitacora_recorta_detalle_a_1000(self):
        registrar_bitacora('t', 'PRUEBA', 'x' * 5000, '10.0.0.1', Rol.ADMIN)
        b = Bitacora.objects.get(accion='PRUEBA')
        self.assertEqual(len(b.detalle), 1000)
        self.assertEqual(b.ip, '10.0.0.1')

    def test_obtener_ip_directa(self):
        req = RequestFactory().get('/', REMOTE_ADDR='192.168.1.20')
        self.assertEqual(obtener_ip(req), '192.168.1.20')


class CatalogosTests(SimpleTestCase):
    def test_especialidades_sin_duplicados(self):
        self.assertEqual(len(ESPECIALIDADES), len(set(ESPECIALIDADES)))

    def test_especialidades_tarde_existen_en_catalogo(self):
        for esp in ESPECIALIDADES_TARDE:
            self.assertIn(esp, ESPECIALIDADES)

    def test_tarde_rechaza_antes_de_mediodia(self):
        self.assertFalse(hora_permitida_para_especialidad(ESP_TARDE, time(11, 59)))

    def test_tarde_acepta_desde_mediodia(self):
        self.assertTrue(hora_permitida_para_especialidad(ESP_TARDE, time(12, 0)))

    def test_especialidad_normal_acepta_manana(self):
        self.assertTrue(hora_permitida_para_especialidad(ESP_GENERAL, time(7, 0)))

    def test_sin_hora_no_bloquea(self):
        self.assertTrue(hora_permitida_para_especialidad(ESP_TARDE, None))
