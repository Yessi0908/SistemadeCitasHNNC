from datetime import date

from app.models import Cita, NotaVAS, Rol

from .datos import ESP_GENERAL, ESP_VAS, HORA_MANANA, MANANA, PruebaAPI, crear_medico, crear_paciente


class VASAPITests(PruebaAPI):
    def setUp(self):
        super().setUp()
        self.vas = crear_paciente(dpi='777', especialidad=ESP_VAS)
        self.otro = crear_paciente(dpi='888', especialidad=ESP_GENERAL)
        self.c = self.cliente(Rol.JURIDICO)

    def test_lista_solo_pacientes_vas(self):
        ids = [p['id'] for p in self.c.get('/api/vas/pacientes/').json()]
        self.assertEqual(ids, [self.vas.id])

    def test_detalle_de_paciente_no_vas(self):
        self.assertEqual(self.c.get(f'/api/vas/paciente/{self.otro.id}/detalle/').status_code, 404)

    def test_nota_muy_corta(self):
        r = self.c.post(f'/api/vas/paciente/{self.vas.id}/notas/', {'texto': 'ok'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_ciclo_de_nota(self):
        r = self.c.post(f'/api/vas/paciente/{self.vas.id}/notas/', {'texto': 'Declaración de la víctima'}, format='json')
        self.assertEqual(r.status_code, 201)
        nota = NotaVAS.objects.get(paciente=self.vas)
        r = self.c.post(f'/api/vas/notas/{nota.id}/editar/', {'texto': 'Declaración corregida'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.post(f'/api/vas/notas/{nota.id}/confirmar/').status_code, 200)
        nota.refresh_from_db()
        self.assertTrue(nota.lista)
        self.assertEqual(nota.confirmada_por, 't_juridico')

    def test_nota_confirmada_es_inmutable_por_api(self):
        nota = NotaVAS.objects.create(paciente=self.vas, texto='Texto final', lista=True)
        r = self.c.post(f'/api/vas/notas/{nota.id}/editar/', {'texto': 'Intento de cambio'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.c.post(f'/api/vas/notas/{nota.id}/confirmar/').status_code, 403)


class DocumentosTests(PruebaAPI):
    def setUp(self):
        super().setUp()
        self.p = crear_paciente(fecha_ingreso=date.today())

    def assertPDF(self, r):
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_carnet(self):
        self.assertPDF(self.cliente(Rol.REGISTROS).get(f'/api/pacientes/{self.p.id}/carnet/'))

    def test_hoja_expediente(self):
        self.assertPDF(self.cliente(Rol.REGISTROS).get(f'/api/pacientes/{self.p.id}/hoja_expediente/'))

    def test_constancia(self):
        self.assertPDF(self.cliente(Rol.REGISTROS).get(f'/api/pacientes/{self.p.id}/constancia/'))

    def test_juridico_no_imprime_carnet(self):
        self.assertEqual(self.cliente(Rol.JURIDICO).get(f'/api/pacientes/{self.p.id}/carnet/').status_code, 403)

    def test_registro_diario_incluye_citas_e_ingresos(self):
        Cita.objects.create(paciente=self.p, medico=crear_medico(), fecha=date.today(), hora=HORA_MANANA, especialidad=ESP_GENERAL)
        crear_paciente(dpi='999', nombre='Ingreso', fecha_ingreso=date.today())
        data = self.cliente(Rol.REGISTROS).get(f'/api/registro-diario/?fecha={date.today()}').json()
        estados = sorted(d['estado'] for d in data['detalles'])
        self.assertEqual(estados, ['Confirmada', 'Ingreso'])
        self.assertEqual(data['registro']['total_pacientes'], 2)

    def test_registro_diario_fecha_futura(self):
        r = self.cliente(Rol.REGISTROS).get(f'/api/registro-diario/?fecha={MANANA}')
        self.assertEqual(r.status_code, 400)

    def test_registro_diario_pdf(self):
        self.assertPDF(self.cliente(Rol.REGISTROS).put(f'/api/registro-diario/?fecha={date.today()}'))

    def test_exportar_excel(self):
        r = self.cliente(Rol.ESTADISTICA).get('/api/estadistica/exportar_excel/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r['Content-Type'])
        self.assertTrue(r.content.startswith(b'PK'))
