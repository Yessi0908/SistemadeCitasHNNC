from datetime import date
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .catalogos import ESPECIALIDADES, ESTADOS_CITA, MENSAJE_HORA_TARDE, hora_permitida_para_especialidad
from .models import (
    Paciente, Consulta, Cita, Bitacora, ExpedienteVAS, NotaVAS,
    EstadisticaRegistro, RegistroDiario, RegistroDiarioDetalle, Medico,
)

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'rol', 'first_name', 'last_name', 'is_active', 'activo_sistema', 'estado']
        read_only_fields = ['id', 'estado']

    def get_estado(self, obj):
        if obj.activo_sistema and obj.is_active:
            return 'Activo'
        return 'Bloqueado'


class UsuarioDetalleAdminSerializer(serializers.ModelSerializer):
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'rol', 'first_name', 'last_name',
            'is_active', 'activo_sistema', 'estado', 'clave_referencia',
        ]

    def get_estado(self, obj):
        if obj.activo_sistema and obj.is_active:
            return 'Activo'
        return 'Bloqueado'


class UsuarioCrearSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ['username', 'password', 'rol', 'first_name', 'last_name']

    def validate_username(self, value):
        nombre = (value or '').strip()
        if not nombre:
            raise serializers.ValidationError('El usuario es obligatorio.')
        if Usuario.objects.filter(username__iexact=nombre).exists():
            raise serializers.ValidationError('Ya existe un usuario con ese nombre. No se permiten duplicados.')
        return nombre

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.clave_referencia = password
        user.save()
        return user


class PacienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    edad_texto = serializers.CharField(read_only=True)

    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = ['numero_expediente', 'creado', 'actualizado', 'edad_anios', 'edad_meses', 'edad_dias']

    def validate_fecha_nacimiento(self, value):
        if value and value > date.today():
            raise serializers.ValidationError('La fecha de nacimiento no puede ser futura.')
        return value

    def validate_fecha_ingreso(self, value):
        if value and value > date.today():
            raise serializers.ValidationError('La fecha de ingreso no puede ser futura.')
        return value

    def validate_dpi(self, value):
        dpi = ''.join(ch for ch in str(value or '') if ch.isalnum())
        if not dpi:
            raise serializers.ValidationError('El DPI es obligatorio.')
        qs = Paciente.objects.filter(dpi__iexact=dpi)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe un paciente registrado con ese DPI.')
        return dpi


class MedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medico
        fields = '__all__'

    def validate_especialidad(self, value):
        if value not in ESPECIALIDADES:
            raise serializers.ValidationError('Especialidad no válida.')
        return value

    def validate(self, data):
        nombre = (data.get('nombre') or getattr(self.instance, 'nombre', '') or '').strip()
        especialidad = data.get('especialidad') or getattr(self.instance, 'especialidad', '')
        if nombre:
            data['nombre'] = nombre
            qs = Medico.objects.filter(nombre__iexact=nombre, especialidad=especialidad)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'nombre': 'Ya existe un médico con ese nombre en la misma especialidad.',
                })
        return data


class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)

    class Meta:
        model = Consulta
        fields = '__all__'


class CitaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    numero_expediente = serializers.CharField(source='paciente.numero_expediente', read_only=True)

    class Meta:
        model = Cita
        fields = '__all__'
        read_only_fields = ['medico_nombre']

    def validate_fecha(self, value):
        if value < date.today():
            raise serializers.ValidationError('La cita solo puede agendarse desde el día de hoy en adelante.')
        return value

    def validate_especialidad(self, value):
        if value and value not in ESPECIALIDADES:
            raise serializers.ValidationError('Especialidad no válida.')
        return value

    def validate_estado(self, value):
        if value not in ESTADOS_CITA:
            raise serializers.ValidationError('Estado de cita no válido.')
        return value

    def validate(self, data):
        medico = data.get('medico') or getattr(self.instance, 'medico', None)
        especialidad = data.get('especialidad') or getattr(self.instance, 'especialidad', None)
        hora = data.get('hora') if 'hora' in data else getattr(self.instance, 'hora', None)
        if not medico:
            raise serializers.ValidationError({'medico': 'Debe seleccionar el médico que atenderá.'})
        if especialidad and medico.especialidad != especialidad:
            raise serializers.ValidationError({'medico': 'El médico no corresponde a la especialidad seleccionada.'})
        if not data.get('especialidad'):
            data['especialidad'] = medico.especialidad
            especialidad = medico.especialidad
        if not hora_permitida_para_especialidad(especialidad, hora):
            raise serializers.ValidationError({'hora': MENSAJE_HORA_TARDE})
        return data

    def create(self, validated_data):
        medico = validated_data.get('medico')
        if medico:
            validated_data['medico_nombre'] = medico.nombre
        return super().create(validated_data)

    def update(self, instance, validated_data):
        medico = validated_data.get('medico', instance.medico)
        if medico:
            validated_data['medico_nombre'] = medico.nombre
        return super().update(instance, validated_data)


class BitacoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bitacora
        fields = '__all__'


class VASSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    dpi = serializers.CharField(source='paciente.dpi', read_only=True)

    class Meta:
        model = ExpedienteVAS
        fields = '__all__'


class NotaVASSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaVAS
        fields = '__all__'
        read_only_fields = ['lista', 'creado_por', 'creado', 'confirmada_por', 'confirmada']


class EstadisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadisticaRegistro
        fields = '__all__'


class RegistroDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroDiario
        fields = '__all__'


class RegistroDiarioDetalleSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.nombre_completo', read_only=True)
    expediente = serializers.CharField(source='paciente.numero_expediente', read_only=True)

    class Meta:
        model = RegistroDiarioDetalle
        fields = '__all__'
