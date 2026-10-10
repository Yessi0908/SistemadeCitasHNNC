from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import Bitacora, Rol

from .datos import CLAVE_PRUEBA, PruebaAPI, Usuario


class LoginTests(PruebaAPI):
    def login(self, username, password=CLAVE_PRUEBA):
        return APIClient().post('/api/auth/login/', {'username': username, 'password': password}, format='json')

    def test_login_correcto_entrega_tokens(self):
        r = self.login('t_registros')
        self.assertEqual(r.status_code, 200)
        for campo in ('access', 'refresh', 'rol', 'username'):
            self.assertIn(campo, r.json())
        self.assertEqual(r.json()['rol'], Rol.REGISTROS)
        self.assertTrue(Bitacora.objects.filter(usuario='t_registros', accion='LOGIN_OK').exists())

    def test_clave_incorrecta(self):
        r = self.login('t_registros', 'incorrecta')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json(), {'error': 'Credenciales inválidas'})
        self.assertEqual(Usuario.objects.get(username='t_registros').intentos_fallidos, 1)
        self.assertTrue(Bitacora.objects.filter(accion='LOGIN_FALLIDO').exists())

    def test_usuario_inexistente_mismo_mensaje(self):
        r = self.login('nadie', 'x')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json(), {'error': 'Credenciales inválidas'})

    def test_bloqueo_tras_intentos_fallidos(self):
        for _ in range(settings.MAX_INTENTOS_LOGIN):
            self.login('t_archivo', 'incorrecta')
        u = Usuario.objects.get(username='t_archivo')
        self.assertIsNotNone(u.bloqueado_hasta)
        r = self.login('t_archivo')
        self.assertEqual(r.status_code, 403)

    def test_bloqueo_expirado_permite_ingresar(self):
        Usuario.objects.filter(username='t_archivo').update(bloqueado_hasta=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.login('t_archivo').status_code, 200)

    def test_usuario_inactivo_no_ingresa(self):
        Usuario.objects.filter(username='t_juridico').update(activo_sistema=False)
        self.assertEqual(self.login('t_juridico').status_code, 403)

    def test_login_exitoso_reinicia_contador(self):
        self.login('t_archivo', 'incorrecta')
        self.login('t_archivo')
        self.assertEqual(Usuario.objects.get(username='t_archivo').intentos_fallidos, 0)


class SesionTests(PruebaAPI):
    def test_logout_invalida_refresh(self):
        tokens = APIClient().post('/api/auth/login/', {'username': 't_admin', 'password': CLAVE_PRUEBA}, format='json').json()
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        self.assertEqual(c.post('/api/auth/logout/', {'refresh': tokens['refresh']}, format='json').status_code, 200)
        r = APIClient().post('/api/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_token_invalido_rechazado(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION='Bearer token.falso.123')
        self.assertEqual(c.get('/api/pacientes/').status_code, 401)

    def test_perfil(self):
        r = self.cliente(Rol.ESTADISTICA).get('/api/auth/perfil/')
        self.assertEqual(r.json()['rol'], Rol.ESTADISTICA)
