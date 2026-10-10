from datetime import date

from app.models import Bitacora, Cita, Paciente, Rol

from .datos import (
    AYER, ESP_GENERAL, ESP_TARDE, HORA_MANANA, MANANA, PACIENTE_VALIDO,
    PruebaAPI, crear_medico, crear_paciente,
)


class PacientesAPITests(PruebaAPI):
    def test_crear_paciente_asigna_expediente(self):
        r = self.cliente(Rol.REGISTROS).post('/api/pacientes/', PACIENTE_VALIDO, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertRegex(r.json()['numero_expediente'], r'^263-\d{4}-0001-00$')
        self.assertTrue(Bitacora.objects.filter(accion='CREAR_PACIENTE').exists())

    def test_crear_paciente_sin_fecha_ingreso_usa_hoy(self):
        datos = {k: v for k, v in PACIENTE_VALIDO.items() if k != 'fecha_ingreso'}
        r = self.cliente(Rol.REGISTROS).post('/api/pacientes/', datos, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['fecha_ingreso'], str(date.today()))

    def test_expediente_no_se_puede_alterar(self):
        p = crear_paciente()
        original = p.numero_expediente
        self.cliente(Rol.REGISTROS).patch(f'/api/pacientes/{p.id}/', {'numero_expediente': 'HACK'}, format='json')
        p.refresh_from_db()
        self.assertEqual(p.numero_expediente, original)

    def test_cambio_de_estado_queda_en_bitacora(self):
        p = crear_paciente()
        r = self.cliente(Rol.REGISTROS).patch(f'/api/pacientes/{p.id}/', {'estado_paciente': 'Control'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Bitacora.objects.filter(accion='CAMBIAR_ESTADO_PACIENTE').exists())

    def test_eliminar_paciente(self):
        p = crear_paciente()
        r = self.cliente(Rol.ADMIN).delete(f'/api/pacientes/{p.id}/')
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Paciente.objects.filter(pk=p.pk).exists())
        self.assertTrue(Bitacora.objects.filter(accion='ELIMINAR_PACIENTE').exists())

    def test_busqueda_por_dpi_parcial(self):
        crear_paciente(dpi='2999888770101')
        crear_paciente(dpi='1111111110101', nombre='Otro')
        r = self.cliente(Rol.REGISTROS).get('/api/registros/buscar/?q=29998')
        self.assertEqual(len(r.json()), 1)

    def test_busqueda_vacia(self):
        self.assertEqual(self.cliente(Rol.REGISTROS).get('/api/registros/buscar/?q=').json(), [])

    def test_resumen_de_citas_separa_proximas_e_historial(self):
        p, m = crear_paciente(), crear_medico()
        Cita.objects.create(paciente=p, medico=m, fecha=MANANA, hora=HORA_MANANA, especialidad=ESP_GENERAL)
        Cita.objects.create(paciente=p, medico=m, fecha=AYER, hora=HORA_MANANA, especialidad=ESP_GENERAL, estado='Atendida')
        data = self.cliente(Rol.ARCHIVO).get(f'/api/pacientes/{p.id}/citas_resumen/').json()
        self.assertEqual(len(data['proximas']), 1)
        self.assertEqual(len(data['historial']), 1)

    def test_catalogos_solo_medicos_activos(self):
        crear_medico('Activo')
        crear_medico('Inactivo', activo=False)
        data = self.cliente(Rol.REGISTROS).get('/api/catalogos/paciente/').json()
        self.assertEqual([m['nombre'] for m in data['medicos']], ['Activo'])
        self.assertIn(ESP_GENERAL, data['especialidades'])


class CitasAPITests(PruebaAPI):
    def setUp(self):
        super().setUp()
        self.paciente = crear_paciente()
        self.medico = crear_medico()

    def cita(self, **cambios):
        datos = {
            'paciente': self.paciente.id, 'medico': self.medico.id, 'fecha': str(MANANA),
            'hora': '09:00', 'especialidad': ESP_GENERAL,
        }
        datos.update(cambios)
        return self.cliente(Rol.REGISTROS).post('/api/citas/', datos, format='json')

    def test_agendar_cita(self):
        r = self.cita()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['medico_nombre'], self.medico.nombre)
        self.assertTrue(Bitacora.objects.filter(accion='CREAR_CITA').exists())

    def test_rechaza_fecha_pasada(self):
        self.assertEqual(self.cita(fecha=str(AYER)).status_code, 400)

    def test_rechaza_tarde_en_la_manana(self):
        m = crear_medico('Lic. Tarde', ESP_TARDE)
        self.assertEqual(self.cita(medico=m.id, especialidad=ESP_TARDE, hora='08:00').status_code, 400)
        self.assertEqual(self.cita(medico=m.id, especialidad=ESP_TARDE, hora='13:00').status_code, 201)

    def test_alertas_de_manana(self):
        self.cita()
        self.cita(fecha=str(date.today()))
        data = self.cliente(Rol.REGISTROS).get('/api/citas/alertas/').json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['fecha'], str(MANANA))

    def test_archivo_filtra_citas_por_fecha(self):
        self.cita()
        r = self.cliente(Rol.ARCHIVO).get(f'/api/archivo/citas/?fecha={MANANA}')
        self.assertEqual(len(r.json()), 1)
