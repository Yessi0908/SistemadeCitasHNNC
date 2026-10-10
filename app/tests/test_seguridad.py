"""Pruebas de los controles de seguridad (confidencialidad, integridad, disponibilidad)."""
from datetime import date

from rest_framework.test import APIClient

from app.models import Bitacora, Rol

from .datos import CARGAS_XSS, CLAVE_PRUEBA, ESP_VAS, PACIENTE_VALIDO, PruebaAPI, Usuario, crear_paciente


class XSSTests(PruebaAPI):
    def test_rechaza_html_en_paciente(self):
        for carga in CARGAS_XSS:
            with self.subTest(carga=carga):
                r = self.cliente(Rol.REGISTROS).post(
                    '/api/pacientes/', {**PACIENTE_VALIDO, 'primer_nombre': carga}, format='json',
                )
                self.assertEqual(r.status_code, 400)

    def test_rechaza_html_en_medico(self):
        r = self.cliente(Rol.ADMIN).post(
            '/api/medicos/', {'nombre': CARGAS_XSS[1], 'especialidad': 'Medicina General (MG)'}, format='json',
        )
        self.assertEqual(r.status_code, 400)

    def test_rechaza_html_en_nota_vas(self):
        p = crear_paciente(especialidad=ESP_VAS)
        r = self.cliente(Rol.JURIDICO).post(f'/api/vas/paciente/{p.id}/notas/', {'texto': CARGAS_XSS[0]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_acepta_texto_normal_con_simbolos(self):
        r = self.cliente(Rol.REGISTROS).post(
            '/api/pacientes/', {**PACIENTE_VALIDO, 'direccion': '5a. Av. 3-20 "Zona 1" & Col. O\'Hara'}, format='json',
        )
        self.assertEqual(r.status_code, 201, r.content)


class ContrasenasTests(PruebaAPI):
    def crear(self, password):
        return self.cliente(Rol.ADMIN).post(
            '/api/usuarios/', {'username': 'nuevo', 'password': password, 'rol': 'archivo'}, format='json',
        )

    def test_rechaza_contrasenas_debiles(self):
        for debil in ('12345678', 'password', 'abc123', 'hospital'):
            with self.subTest(clave=debil):
                self.assertEqual(self.crear(debil).status_code, 400)

    def test_referencia_no_se_guarda_en_texto_plano(self):
        self.crear('Referencia#Segura77')
        u = Usuario.objects.get(username='nuevo')
        self.assertNotIn('Referencia#Segura77', u.clave_referencia)


class LoginSeguroTests(PruebaAPI):
    def login(self, username, password, **extra):
        return APIClient().post('/api/auth/login/', {'username': username, 'password': password}, format='json', **extra)

    def test_no_revela_cuenta_inactiva_sin_clave_correcta(self):
        Usuario.objects.filter(username='t_juridico').update(activo_sistema=False)
        inactivo = self.login('t_juridico', 'incorrecta')
        inexistente = self.login('no_existe', 'incorrecta')
        self.assertEqual(inactivo.status_code, inexistente.status_code)
        self.assertEqual(inactivo.json(), inexistente.json())

    def test_limite_de_intentos_por_ip(self):
        codigos = [self.login(f'falso{i}', 'x').status_code for i in range(15)]
        self.assertIn(429, codigos)

    def test_ip_de_bitacora_no_se_falsifica(self):
        self.login('xff', 'x', HTTP_X_FORWARDED_FOR='203.0.113.66')
        self.assertNotEqual(Bitacora.objects.get(usuario='xff').ip, '203.0.113.66')


class ExposicionTests(PruebaAPI):
    def test_esquema_api_no_es_publico(self):
        self.assertIn(APIClient().get('/api/schema/').status_code, (401, 403, 404))

    def test_esquema_api_para_admin_con_sesion(self):
        c = APIClient()
        c.login(username='t_admin', password=CLAVE_PRUEBA)
        self.assertEqual(c.get('/api/schema/').status_code, 200)

    def test_cabecera_csp(self):
        r = self.client.get('/login/')
        self.assertIn("default-src 'self'", r.get('Content-Security-Policy', ''))

    def test_cabeceras_basicas(self):
        r = self.client.get('/login/')
        self.assertEqual(r['X-Frame-Options'], 'DENY')
        self.assertEqual(r['X-Content-Type-Options'], 'nosniff')
        self.assertIn('no-store', r['Cache-Control'])


class DisponibilidadTests(PruebaAPI):
    def test_registro_diario_paciente_inexistente(self):
        r = self.cliente(Rol.REGISTROS).post(
            '/api/registro-diario/', {'fecha': str(date.today()), 'paciente_id': 999999}, format='json',
        )
        self.assertEqual(r.status_code, 404)

    def test_registro_diario_sin_paciente(self):
        r = self.cliente(Rol.REGISTROS).post('/api/registro-diario/', {'fecha': str(date.today())}, format='json')
        self.assertEqual(r.status_code, 400)
