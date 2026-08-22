# Catalogo oficial HNNCJ — formato: Nombre (SIGLA)
from datetime import time

ESPECIALIDADES = [
    'Medicina Interna (MI)',
    'Violencia y Abuso Sexual (VAS)',
    'Medicina General (MG)',
    'Medicina General Tarde (MGT)',
    'Traumatología Mujeres (TM)',
    'Traumatología Hombres (TH)',
    'Pediatría (P)',
    'Psicología (PS)',
    'Psicología Tarde (PST)',
    'Psiquiatría (PQ)',
    'Traumatología Pediátrica (TP)',
    'Nutrición (N)',
    'Alto Riesgo (ARO)',
    'Ginecología (GINE)',
    'Cirugía Mujeres (CM)',
    'Cirugía Hombres (CH)',
    'Odontología (ODO)',
    'Preoperatorio (PREOP)',
    'Nefrología (NEFRO)',
    'Electrocardiograma (EKG)',
    'Videocirugía (VC)',
]

# Solo se pueden agendar a partir de las 12:00 p.m.
ESPECIALIDADES_TARDE = [
    'Psicología Tarde (PST)',
    'Medicina General Tarde (MGT)',
]

HORA_MINIMA_TARDE = time(12, 0)
MENSAJE_HORA_TARDE = (
    'Las especialidades de la tarde (PST y MGT) solo se pueden agendar '
    'a partir de las 12:00 p.m.'
)


def especialidad_es_tarde(especialidad):
    return especialidad in ESPECIALIDADES_TARDE


def hora_permitida_para_especialidad(especialidad, hora):
    if not especialidad_es_tarde(especialidad) or hora is None:
        return True
    return hora >= HORA_MINIMA_TARDE

ESTADOS_PACIENTE = [
    'Control',
    'Primera vez',
]

ESTADOS_CIVILES = [
    'Soltero(a)',
    'Casado(a)',
    'Viudo(a)',
]

ESTADOS_CITA = [
    'Confirmada',
    'Cancelada',
    'Atendida',
]
