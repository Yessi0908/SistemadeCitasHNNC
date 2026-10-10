from django.test import TestCase

from app.models import Rol
from app.serializers import (
    CitaSerializer, MedicoSerializer, PacienteSerializer, UsuarioCrearSerializer,
)

from .datos import (
    AYER, ESP_GENERAL, ESP_TARDE, MANANA, PACIENTE_VALIDO,
    crear_medico, crear_paciente, crear_usuario,
)


class PacienteSerializerTests(TestCase):
    def test_datos_validos(self):
        s = PacienteSerializer(data=PACIENTE_VALIDO)
        self.assertTrue(s.is_valid(), s.errors)

    def test_dpi_se_normaliza(self):
        s = PacienteSerializer(data=PACIENTE_VALIDO)
        s.is_valid()
        self.assertEqual(s.validated_data['dpi'], '2547896320101')

    def test_dpi_duplicado(self):
        crear_paciente(dpi='2547896320101')
        s = PacienteSerializer(data=PACIENTE_VALIDO)
        self.assertFalse(s.is_valid())
        self.assertIn('dpi', s.errors)

    def test_fecha_nacimiento_futura(self):
        s = PacienteSerializer(data={**PACIENTE_VALIDO, 'fecha_nacimiento': str(MANANA)})
        self.assertFalse(s.is_valid())
        self.assertIn('fecha_nacimiento', s.errors)

    def test_fecha_ingreso_futura(self):
        s = PacienteSerializer(data={**PACIENTE_VALIDO, 'fecha_ingreso': str(MANANA)})
        self.assertFalse(s.is_valid())
        self.assertIn('fecha_ingreso', s.errors)


class CitaSerializerTests(TestCase):
    def setUp(self):
        self.paciente = crear_paciente()
        self.medico = crear_medico()

    def datos(self, **cambios):
        base = {
            'paciente': self.paciente.id, 'medico': self.medico.id, 'fecha': str(MANANA),
            'hora': '09:00', 'especialidad': ESP_GENERAL, 'estado': 'Confirmada',
        }
        base.update(cambios)
        return base

    def test_cita_valida(self):
        s = CitaSerializer(data=self.datos())
        self.assertTrue(s.is_valid(), s.errors)

    def test_fecha_pasada(self):
        s = CitaSerializer(data=self.datos(fecha=str(AYER)))
        self.assertFalse(s.is_valid())
        self.assertIn('fecha', s.errors)

    def test_medico_de_otra_especialidad(self):
        s = CitaSerializer(data=self.datos(especialidad='Pediatría (P)'))
        self.assertFalse(s.is_valid())
        self.assertIn('medico', s.errors)

    def test_sin_medico(self):
        s = CitaSerializer(data=self.datos(medico=None))
        self.assertFalse(s.is_valid())
        self.assertIn('medico', s.errors)

    def test_especialidad_tarde_en_la_manana(self):
        medico_tarde = crear_medico('Lic. Rosa Paz', ESP_TARDE)
        s = CitaSerializer(data=self.datos(medico=medico_tarde.id, especialidad=ESP_TARDE, hora='10:00'))
        self.assertFalse(s.is_valid())
        self.assertIn('hora', s.errors)

    def test_estado_invalido(self):
        s = CitaSerializer(data=self.datos(estado='Perdida'))
        self.assertFalse(s.is_valid())
        self.assertIn('estado', s.errors)


class MedicoSerializerTests(TestCase):
    def test_especialidad_invalida(self):
        s = MedicoSerializer(data={'nombre': 'Dr. X', 'especialidad': 'Cardiología'})
        self.assertFalse(s.is_valid())

    def test_nombre_duplicado_misma_especialidad(self):
        crear_medico('Dr. Carlos Ruiz', ESP_GENERAL)
        s = MedicoSerializer(data={'nombre': 'dr. carlos ruiz', 'especialidad': ESP_GENERAL})
        self.assertFalse(s.is_valid())
        self.assertIn('nombre', s.errors)

    def test_mismo_nombre_otra_especialidad(self):
        crear_medico('Dr. Carlos Ruiz', ESP_GENERAL)
        s = MedicoSerializer(data={'nombre': 'Dr. Carlos Ruiz', 'especialidad': 'Pediatría (P)'})
        self.assertTrue(s.is_valid(), s.errors)


class UsuarioCrearSerializerTests(TestCase):
    def test_usuario_duplicado_sin_importar_mayusculas(self):
        crear_usuario('Registros1', Rol.REGISTROS)
        s = UsuarioCrearSerializer(data={'username': 'registros1', 'password': 'Otra#Clave2026', 'rol': 'registros'})
        self.assertFalse(s.is_valid())
        self.assertIn('username', s.errors)
