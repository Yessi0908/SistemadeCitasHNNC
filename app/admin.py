from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Paciente, Consulta, Cita, Bitacora, Medico,
    ExpedienteVAS, EstadisticaRegistro, RegistroDiario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'rol', 'is_active', 'activo_sistema']
    list_filter = ['rol', 'is_active', 'activo_sistema']
    search_fields = ['username', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (('Hospital', {'fields': ('rol', 'activo_sistema', 'clave_referencia')}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('rol',)}),)


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'especialidad', 'activo', 'creado']
    list_filter = ['especialidad', 'activo']
    search_fields = ['nombre']


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['numero_expediente', 'ver_nombre_completo', 'dpi', 'especialidad', 'estado_paciente']
    search_fields = ['numero_expediente', 'dpi', 'primer_nombre', 'primer_apellido']
    list_filter = ['especialidad', 'estado_paciente', 'sexo']
    ordering = ['numero_expediente']

    @admin.display(description='Nombre completo')
    def ver_nombre_completo(self, obj):
        return obj.nombre_completo


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'hora', 'paciente', 'medico', 'especialidad', 'estado']
    list_filter = ['fecha', 'estado', 'especialidad']
    search_fields = ['paciente__numero_expediente', 'paciente__dpi', 'paciente__primer_nombre']
    ordering = ['-fecha', '-hora']


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'paciente', 'especialidad', 'medico']
    list_filter = ['fecha', 'especialidad']
    search_fields = ['paciente__numero_expediente']


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'usuario', 'rol', 'accion', 'detalle', 'ip']
    list_filter = ['accion', 'rol']
    search_fields = ['usuario', 'detalle']
    ordering = ['-fecha']


admin.site.register(ExpedienteVAS)
admin.site.register(EstadisticaRegistro)
admin.site.register(RegistroDiario)

admin.site.site_header = 'Hospital Nicolasa Cruz Jalapa'
admin.site.site_title = 'Admin HNNCJ'
admin.site.index_title = 'Base de datos del sistema'
