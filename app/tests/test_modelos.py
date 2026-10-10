from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from app.models import Cita, NotaVAS, Paciente

from .datos import ESP_TARDE, HORA_MANANA, MANANA, crear_medico, crear_paciente
from .test_utilidades import hace_anios


class PacienteModeloTests(TestCase):
    def test_edad_se_calcula_al_guardar(self):
        p = crear_paciente(fecha_nacimiento=hace_anios(25))
        self.assertEqual((p.edad_anios, p.edad_meses, p.edad_dias), (25, 0, 0))

    def test_nombre_completo_omite_vacios(self):
        p = crear_paciente(nombre='Ana', apellido='Gómez')
        self.assertEqual(p.nombre_completo, 'Ana Gómez')

    def test_edad_texto_sin_fecha(self):
        self.assertEqual(crear_paciente().edad_texto, '—')

    def test_dpi_unico(self):
        crear_paciente(dpi='555')
        with self.assertRaises(IntegrityError):
            Paciente.objects.create(primer_nombre='X', primer_apellido='Y', dpi='555', numero_expediente='otro')


class CitaModeloTests(TestCase):
    def test_especialidad_tarde_antes_de_mediodia_es_invalida(self):
        cita = Cita(
            paciente=crear_paciente(), medico=crear_medico(especialidad=ESP_TARDE),
            fecha=MANANA, hora=HORA_MANANA, especialidad=ESP_TARDE,
        )
        with self.assertRaises(ValidationError):
            cita.clean()


class NotaVASModeloTests(TestCase):
    def setUp(self):
        self.nota = NotaVAS.objects.create(paciente=crear_paciente(), texto='Declaración inicial', lista=True)

    def test_nota_confirmada_no_se_modifica(self):
        self.nota.texto = 'Cambio no autorizado'
        with self.assertRaises(ValidationError):
            self.nota.save()

    def test_nota_confirmada_no_se_elimina(self):
        with self.assertRaises(ValidationError), transaction.atomic():
            self.nota.delete()
        self.assertTrue(NotaVAS.objects.filter(pk=self.nota.pk).exists())
