from rest_framework.test import APIClient

from app.models import Rol

from .datos import PruebaAPI

A, R, AR, E, J = Rol.ADMIN, Rol.REGISTROS, Rol.ARCHIVO, Rol.ESTADISTICA, Rol.JURIDICO

# (método, ruta, roles con acceso). El resto de roles debe recibir 403.
MATRIZ = [
    ('get', '/api/pacientes/', {A, R, AR, E}),
    ('get', '/api/citas/', {A, R, AR}),
    ('get', '/api/usuarios/', {A}),
    ('get', '/api/bitacora/', {A}),
    ('get', '/api/vas/', {A, J}),
    ('get', '/api/estadistica/resumen_tablas/', {A, E}),
    ('get', '/api/registros/buscar/?q=x', {A, R}),
    ('get', '/api/archivo/buscar/?q=x', {A, AR}),
    ('get', '/api/registro-diario/', {A, R, AR}),
    ('post', '/api/respaldo/', {A}),
]


class MatrizPermisosTests(PruebaAPI):
    def test_anonimo_recibe_401(self):
        for metodo, ruta, _ in MATRIZ:
            with self.subTest(ruta=ruta):
                r = getattr(APIClient(), metodo)(ruta)
                self.assertEqual(r.status_code, 401)

    def test_acceso_por_rol(self):
        for metodo, ruta, permitidos in MATRIZ:
            for rol in (A, R, AR, E, J):
                with self.subTest(ruta=ruta, rol=rol):
                    r = getattr(self.cliente(rol), metodo)(ruta, format='json')
                    if rol in permitidos:
                        self.assertNotIn(r.status_code, (401, 403))
                    else:
                        self.assertEqual(r.status_code, 403)

    def test_archivo_solo_lectura_en_pacientes(self):
        r = self.cliente(AR).post('/api/pacientes/', {'primer_apellido': 'X', 'primer_nombre': 'Y', 'dpi': '1'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_estadistica_no_crea_pacientes(self):
        r = self.cliente(E).post('/api/pacientes/', {'primer_apellido': 'X', 'primer_nombre': 'Y', 'dpi': '1'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_archivo_no_agenda_citas(self):
        r = self.cliente(AR).post('/api/citas/', {}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_solo_admin_crea_medicos(self):
        datos = {'nombre': 'Dr. Prueba', 'especialidad': 'Medicina General (MG)'}
        self.assertEqual(self.cliente(R).post('/api/medicos/', datos, format='json').status_code, 403)
        self.assertEqual(self.cliente(A).post('/api/medicos/', datos, format='json').status_code, 201)
