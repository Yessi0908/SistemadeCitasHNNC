# Catalogo oficial HNNCJ — formato: Nombre (SIGLA)
# Estas listas alimentan los selects del panel (vista catalogos_paciente).
from datetime import time

# Especialidades que salen en paciente, cita y médico. Agregar aquí una línea basta.
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


# Subconjunto de ESPECIALIDADES: la cita no puede ser antes de las 12:00.
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

# Estado del paciente en el expediente
ESTADOS_PACIENTE = [
    'Control',
    'Primera vez',
]

# Estado civil del paciente
ESTADOS_CIVILES = [
    'Soltero(a)',
    'Casado(a)',
    'Viudo(a)',
]

# Estado de una cita agendada
ESTADOS_CITA = [
    'Confirmada',
    'Cancelada',
    'Atendida',
]
