from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .catalogos import (
    ESPECIALIDADES, ESTADOS_PACIENTE, ESTADOS_CIVILES, ESTADOS_CITA,
    MENSAJE_HORA_TARDE, hora_permitida_para_especialidad,
)


class Rol(models.TextChoices):
    ADMIN = 'admin', 'Administrador'
    ARCHIVO = 'archivo', 'Archivo'
    REGISTROS = 'registros', 'Registros'
    ESTADISTICA = 'estadistica', 'Estadística'
    JURIDICO = 'juridico', 'Jurídico'


class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ARCHIVO)
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    activo_sistema = models.BooleanField(default=True)
    clave_referencia = models.CharField(
        max_length=128, blank=True,
        help_text='Referencia interna de contraseña visible solo al administrador autenticado.',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Bitacora(models.Model):
    usuario = models.CharField(max_length=150)
    rol = models.CharField(max_length=20, blank=True)
    accion = models.CharField(max_length=100)
    detalle = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Bitácora'


class Medico(models.Model):
    nombre = models.CharField(max_length=120)
    especialidad = models.CharField(
        max_length=100,
        choices=[(e, e) for e in ESPECIALIDADES],
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['especialidad', 'nombre']
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'

    def __str__(self):
        return f'{self.nombre} ({self.especialidad})'


class Paciente(models.Model):
    primer_apellido = models.CharField(max_length=80)
    segundo_apellido = models.CharField(max_length=80, blank=True)
    primer_nombre = models.CharField(max_length=80)
    segundo_nombre = models.CharField(max_length=80, blank=True)
    numero_expediente = models.CharField(max_length=20, unique=True, editable=False)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    lugar_nacimiento = models.CharField(max_length=120, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    edad_anios = models.PositiveSmallIntegerField(default=0)
    edad_meses = models.PositiveSmallIntegerField(default=0)
    edad_dias = models.PositiveSmallIntegerField(default=0)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')], blank=True)
    estado_civil = models.CharField(
        max_length=20, blank=True,
        choices=[(e, e) for e in ESTADOS_CIVILES],
    )
    ocupacion = models.CharField(max_length=100, blank=True)
    nacionalidad = models.CharField(max_length=60, default='Guatemalteca')
    dpi = models.CharField(max_length=20, unique=True, db_index=True)
    nombre_conyuge = models.CharField(max_length=160, blank=True)
    nombre_padre = models.CharField(max_length=160, blank=True)
    nombre_madre = models.CharField(max_length=160, blank=True)
    contacto_emergencia_nombre = models.CharField(max_length=160, blank=True)
    contacto_emergencia_telefono = models.CharField(max_length=30, blank=True)
    fecha_ingreso = models.DateField(default=timezone.now)
    especialidad = models.CharField(
        max_length=100, blank=True,
        choices=[(e, e) for e in ESPECIALIDADES],
    )
    estado_paciente = models.CharField(
        max_length=20, default='Primera vez',
        choices=[(e, e) for e in ESTADOS_PACIENTE],
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['primer_apellido', 'primer_nombre']
        indexes = [
            models.Index(fields=['primer_apellido', 'primer_nombre']),
            models.Index(fields=['numero_expediente']),
        ]

    @property
    def nombre_completo(self):
        partes = [self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido]
        return ' '.join(p for p in partes if p).strip()

    @property
    def edad_texto(self):
        if not self.fecha_nacimiento:
            return '—'
        return f'{self.edad_anios} años, {self.edad_meses} meses, {self.edad_dias} días'


class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(null=True, blank=True)
    especialidad = models.CharField(max_length=100)
    medico = models.CharField(max_length=120, blank=True)
    motivo = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    reprogramada = models.BooleanField(default=False)
    creado_por = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['-fecha', '-hora']


class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    medico = models.ForeignKey(Medico, on_delete=models.PROTECT, related_name='citas', null=True, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    especialidad = models.CharField(max_length=100)
    estado = models.CharField(
        max_length=20,
        default='Confirmada',
        choices=[(e, e) for e in ESTADOS_CITA],
    )
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['fecha', 'hora']

    def clean(self):
        super().clean()
        if not hora_permitida_para_especialidad(self.especialidad, self.hora):
            raise ValidationError({'hora': MENSAJE_HORA_TARDE})


class RegistroDiario(models.Model):
    fecha = models.DateField(unique=True, default=timezone.now)
    total_pacientes = models.PositiveIntegerField(default=0)
    generado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro diario'


class RegistroDiarioDetalle(models.Model):
    registro = models.ForeignKey(RegistroDiario, on_delete=models.CASCADE, related_name='detalles')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField(default=1)
    especialidad = models.CharField(max_length=100, blank=True)


class ExpedienteVAS(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='vas')
    fecha = models.DateField(default=timezone.now)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50, default='En trámite')
    observaciones = models.TextField(blank=True)
    creado_por = models.CharField(max_length=150, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Expediente VAS'
        ordering = ['-fecha']


class EstadisticaRegistro(models.Model):
    fecha = models.DateField(default=timezone.now)
    categoria = models.CharField(max_length=80)
    valor = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha', 'categoria']


class TokenListaNegra(models.Model):
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    usuario = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)
