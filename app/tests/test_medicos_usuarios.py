from rest_framework.test import APIClient

from app.models import Bitacora, Cita, Medico, Rol

from .datos import CLAVE_PRUEBA, ESP_GENERAL, HORA_MANANA, MANANA, PruebaAPI, Usuario, crear_medico, crear_paciente

JUSTIFICACION = 'Traslado del médico a otro hospital'


class MedicosAPITests(PruebaAPI):
    def test_desactivar_exige_justificacion(self):
        m = crear_medico()
        r = self.cliente(Rol.ADMIN).patch(f'/api/medicos/{m.id}/', {'activo': False}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_desactivar_con_justificacion(self):
        m = crear_medico()
        r = self.cliente(Rol.ADMIN).patch(
            f'/api/medicos/{m.id}/', {'activo': False, 'justificacion': JUSTIFICACION}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Medico.objects.get(pk=m.pk).activo)
        self.assertTrue(Bitacora.objects.filter(accion='DESACTIVAR_MEDICO', detalle__contains=JUSTIFICACION).exists())

    def test_no_elimina_medico_con_citas_abiertas(self):
        m = crear_medico()
        Cita.objects.create(paciente=crear_paciente(), medico=m, fecha=MANANA, hora=HORA_MANANA, especialidad=ESP_GENERAL)
        r = self.cliente(Rol.ADMIN).delete(f'/api/medicos/{m.id}/', {'justificacion': JUSTIFICACION}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_eliminar_conserva_nombre_en_historial(self):
        m = crear_medico('Dr. Histórico')
        cita = Cita.objects.create(
            paciente=crear_paciente(), medico=m, fecha=MANANA, hora=HORA_MANANA,
            especialidad=ESP_GENERAL, estado='Atendida',
        )
        r = self.cliente(Rol.ADMIN).delete(f'/api/medicos/{m.id}/', {'justificacion': JUSTIFICACION}, format='json')
        self.assertEqual(r.status_code, 204)
        cita.refresh_from_db()
        self.assertIsNone(cita.medico)
        self.assertEqual(cita.medico_nombre, 'Dr. Histórico')


class UsuariosAPITests(PruebaAPI):
    NUEVA_CLAVE = 'Archivo#Seguro2026'

    def crear(self, **cambios):
        datos = {'username': 'nuevo_archivo', 'password': self.NUEVA_CLAVE, 'rol': 'archivo'}
        datos.update(cambios)
        return self.cliente(Rol.ADMIN).post('/api/usuarios/', datos, format='json')

    def test_crear_usuario_con_hash(self):
        self.assertEqual(self.crear().status_code, 201)
        u = Usuario.objects.get(username='nuevo_archivo')
        self.assertTrue(u.password.startswith('bcrypt_sha256$'))
        self.assertTrue(u.check_password(self.NUEVA_CLAVE))
        self.assertTrue(Bitacora.objects.filter(accion='CREAR_USUARIO').exists())

    def test_respuesta_no_incluye_contrasena(self):
        r = self.crear()
        self.assertNotIn('password', r.json())
        self.assertNotIn(self.NUEVA_CLAVE, r.content.decode())

    def test_admin_no_se_elimina_a_si_mismo(self):
        yo = self.usuarios[Rol.ADMIN]
        r = self.cliente(Rol.ADMIN).delete(f'/api/usuarios/{yo.id}/', {'justificacion': JUSTIFICACION}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_admin_no_se_bloquea_a_si_mismo(self):
        yo = self.usuarios[Rol.ADMIN]
        self.assertEqual(self.cliente(Rol.ADMIN).post(f'/api/usuarios/{yo.id}/bloquear/').status_code, 400)

    def test_bloquear_y_reactivar(self):
        u = self.usuarios[Rol.ARCHIVO]
        login = lambda: APIClient().post('/api/auth/login/', {'username': u.username, 'password': CLAVE_PRUEBA}, format='json')
        self.cliente(Rol.ADMIN).post(f'/api/usuarios/{u.id}/bloquear/')
        self.assertEqual(login().status_code, 403)
        self.cliente(Rol.ADMIN).post(f'/api/usuarios/{u.id}/reactivar/')
        self.assertEqual(login().status_code, 200)

    def test_ver_datos_exige_clave_admin(self):
        self.crear()
        u = Usuario.objects.get(username='nuevo_archivo')
        r = self.cliente(Rol.ADMIN).post(f'/api/usuarios/{u.id}/ver_datos/', {'contrasena_admin': 'mala'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_ver_datos_muestra_referencia_al_admin(self):
        self.crear()
        u = Usuario.objects.get(username='nuevo_archivo')
        r = self.cliente(Rol.ADMIN).post(
            f'/api/usuarios/{u.id}/ver_datos/', {'contrasena_admin': CLAVE_PRUEBA}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['clave_referencia'], self.NUEVA_CLAVE)
        self.assertTrue(Bitacora.objects.filter(accion='VER_DATOS_USUARIO').exists())
