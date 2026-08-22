from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, FormParser
from openpyxl import Workbook
from django.http import HttpResponse

from .models import (
    Paciente, Consulta, Cita, Bitacora, ExpedienteVAS,
    EstadisticaRegistro, RegistroDiario, RegistroDiarioDetalle,
    TokenListaNegra, Rol, Medico,
)
from .serializers import (
    PacienteSerializer, ConsultaSerializer, CitaSerializer, BitacoraSerializer,
    VASSerializer, EstadisticaSerializer, UsuarioSerializer, UsuarioCrearSerializer,
    RegistroDiarioSerializer, RegistroDiarioDetalleSerializer, MedicoSerializer,
    UsuarioDetalleAdminSerializer,
)
from .permissions import (
    EsAdmin, EsArchivo, EsRegistros, EsEstadistica, EsJuridico, SoloLecturaArchivo,
    EsLecturaArchivoRegistros,
)
from .utils import (
    registrar_bitacora, generar_numero_expediente, usuario_bloqueado, obtener_ip,
)
from . import pdf as generador_pdf

Usuario = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        ip = obtener_ip(request)

        try:
            user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            registrar_bitacora(username, 'LOGIN_FALLIDO', 'Usuario no existe', ip)
            return Response({'error': 'Credenciales inválidas'}, status=401)

        if not user.activo_sistema or not user.is_active:
            return Response({'error': 'Usuario inactivo'}, status=403)

        if usuario_bloqueado(user):
            return Response({'error': 'Cuenta bloqueada temporalmente'}, status=403)

        if not user.check_password(password):
            user.intentos_fallidos += 1
            from django.conf import settings
            if user.intentos_fallidos >= settings.MAX_INTENTOS_LOGIN:
                user.bloqueado_hasta = timezone.now() + timedelta(minutes=settings.BLOQUEO_MINUTOS)
                user.intentos_fallidos = 0
            user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
            registrar_bitacora(username, 'LOGIN_FALLIDO', f'Intento {user.intentos_fallidos}', ip, user.rol)
            return Response({'error': 'Credenciales inválidas'}, status=401)

        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

        refresh = RefreshToken.for_user(user)
        refresh['rol'] = user.rol
        refresh['username'] = user.username
        access = refresh.access_token
        access['rol'] = user.rol

        registrar_bitacora(username, 'LOGIN_OK', '', ip, user.rol)
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'rol': user.rol,
            'username': user.username,
            'user_id': user.id,
            'nombre': user.get_full_name() or user.username,
        })


class LogoutView(APIView):
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        token = request.data.get('refresh')
        if token:
            try:
                rt = RefreshToken(token)
                TokenListaNegra.objects.get_or_create(jti=str(rt['jti']), usuario=request.user.username)
                rt.blacklist()
            except Exception:
                pass
        registrar_bitacora(request.user.username, 'LOGOUT', '', obtener_ip(request), request.user.rol)
        return Response({'mensaje': 'Sesión cerrada'})


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated, SoloLecturaArchivo]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['especialidad', 'estado_paciente']
    search_fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido', 'dpi', 'numero_expediente']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsAuthenticated(), EsRegistros()]
        if self.action == 'destroy':
            return [IsAuthenticated(), EsRegistros()]
        return super().get_permissions()

    def perform_create(self, serializer):
        expediente = generar_numero_expediente()
        paciente = serializer.save(numero_expediente=expediente)
        registrar_bitacora(
            self.request.user.username, 'CREAR_PACIENTE',
            paciente.numero_expediente, obtener_ip(self.request), self.request.user.rol,
        )

    def perform_update(self, serializer):
        paciente = serializer.save()
        registrar_bitacora(
            self.request.user.username, 'ACTUALIZAR_PACIENTE',
            paciente.numero_expediente, obtener_ip(self.request), self.request.user.rol,
        )

    def perform_destroy(self, instance):
        expediente = instance.numero_expediente
        instance.delete()
        registrar_bitacora(
            self.request.user.username, 'ELIMINAR_PACIENTE',
            expediente, obtener_ip(self.request), self.request.user.rol,
        )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def carnet(self, request, pk=None):
        if request.user.rol not in (Rol.REGISTROS, Rol.ADMIN, Rol.ARCHIVO):
            return Response({'error': 'Sin permiso'}, status=403)
        return generador_pdf.generar_carnet(self.get_object())

    @action(detail=True, methods=['get'])
    def hoja_expediente(self, request, pk=None):
        paciente = self.get_object()
        consultas = paciente.consultas.all()
        return generador_pdf.generar_hoja_expediente(paciente, consultas)

    @action(detail=True, methods=['get'])
    def constancia(self, request, pk=None):
        return generador_pdf.generar_constancia_laboral(self.get_object())

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, EsLecturaArchivoRegistros])
    def citas_resumen(self, request, pk=None):
        paciente = self.get_object()
        hoy = date.today()
        citas = Cita.objects.filter(paciente=paciente).order_by('fecha', 'hora')
        proximas = citas.filter(
            fecha__gte=hoy, estado='Confirmada'
        ).order_by('fecha', 'hora')
        historial = citas.exclude(
            pk__in=proximas.values_list('pk', flat=True)
        ).order_by('-fecha', '-hora')
        ser = CitaSerializer
        return Response({
            'paciente_id': paciente.id,
            'numero_expediente': paciente.numero_expediente,
            'nombre': paciente.nombre_completo,
            'edad_texto': paciente.edad_texto,
            'proximas': ser(proximas, many=True).data,
            'historial': ser(historial, many=True).data,
        })


class ConsultaViewSet(viewsets.ModelViewSet):
    queryset = Consulta.objects.select_related('paciente')
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated, SoloLecturaArchivo]
    filterset_fields = ['paciente', 'fecha', 'especialidad']

    def get_permissions(self):
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated(), EsRegistros()]
        if getattr(self.request.user, 'is_authenticated', False) and self.request.user.rol == Rol.ARCHIVO:
            return [IsAuthenticated(), EsArchivo()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user.username)


class MedicoViewSet(viewsets.ModelViewSet):
    queryset = Medico.objects.all()
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['especialidad', 'activo']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), EsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Medico.objects.all()
        if self.request.query_params.get('activos') == '1':
            qs = qs.filter(activo=True)
        esp = self.request.query_params.get('especialidad', '').strip()
        if esp:
            qs = qs.filter(especialidad=esp)
        return qs.order_by('especialidad', 'nombre')

    def perform_create(self, serializer):
        medico = serializer.save()
        registrar_bitacora(
            self.request.user.username, 'CREAR_MEDICO',
            f'{medico.nombre} — {medico.especialidad}', obtener_ip(self.request), self.request.user.rol,
        )

    def perform_update(self, serializer):
        medico = serializer.save()
        registrar_bitacora(
            self.request.user.username, 'ACTUALIZAR_MEDICO',
            f'{medico.nombre} — {medico.especialidad}', obtener_ip(self.request), self.request.user.rol,
        )

    def perform_destroy(self, instance):
        detalle = f'{instance.nombre} — {instance.especialidad}'
        instance.delete()
        registrar_bitacora(
            self.request.user.username, 'ELIMINAR_MEDICO', detalle, obtener_ip(self.request), self.request.user.rol,
        )


class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.select_related('paciente', 'medico')
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['fecha', 'estado', 'especialidad', 'paciente']
    search_fields = ['paciente__numero_expediente', 'paciente__dpi', 'paciente__primer_nombre', 'paciente__primer_apellido']

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated(), EsLecturaArchivoRegistros()]
        return [IsAuthenticated(), EsRegistros()]

    def perform_create(self, serializer):
        cita = serializer.save()
        registrar_bitacora(
            self.request.user.username, 'CREAR_CITA',
            f'{cita.paciente.numero_expediente} {cita.fecha}', obtener_ip(self.request), self.request.user.rol,
        )

    def perform_update(self, serializer):
        cita = serializer.save()
        registrar_bitacora(
            self.request.user.username, 'ACTUALIZAR_CITA',
            f'{cita.paciente.numero_expediente} {cita.fecha}', obtener_ip(self.request), self.request.user.rol,
        )

    def perform_destroy(self, instance):
        detalle = f'{instance.paciente.numero_expediente} {instance.fecha}'
        instance.delete()
        registrar_bitacora(
            self.request.user.username, 'ELIMINAR_CITA', detalle, obtener_ip(self.request), self.request.user.rol,
        )

    @action(detail=False, methods=['get'])
    def alertas(self, request):
        manana = date.today() + timedelta(days=1)
        citas = self.get_queryset().filter(fecha=manana, estado='Confirmada')[:20]
        return Response(CitaSerializer(citas, many=True).data)


class VASViewSet(viewsets.ModelViewSet):
    queryset = ExpedienteVAS.objects.select_related('paciente')
    serializer_class = VASSerializer
    permission_classes = [IsAuthenticated, EsJuridico]
    search_fields = ['paciente__dpi', 'paciente__numero_expediente']

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user.username)


class EstadisticaViewSet(viewsets.ModelViewSet):
    queryset = EstadisticaRegistro.objects.all()
    serializer_class = EstadisticaSerializer
    permission_classes = [IsAuthenticated, EsEstadistica]

    @action(detail=False, methods=['get'])
    def resumen_tablas(self, request):
        # Solo tablas, sin gráficas
        por_especialidad = Paciente.objects.values('especialidad').annotate(
            total=Count('id')
        ).order_by('-total')[:50]
        por_estado = Paciente.objects.values('estado_paciente').annotate(total=Count('id'))
        consultas_mes = Consulta.objects.filter(
            fecha__gte=date.today().replace(day=1)
        ).values('especialidad').annotate(total=Count('id'))
        return Response({
            'pacientes_por_especialidad': list(por_especialidad),
            'pacientes_por_estado': list(por_estado),
            'consultas_mes': list(consultas_mes),
        })

    @action(detail=False, methods=['get'])
    def exportar_excel(self, request):
        wb = Workbook()
        ws = wb.active
        ws.title = 'Estadísticas'
        ws.append(['Categoría', 'Valor', 'Cantidad', 'Fecha'])
        for e in EstadisticaRegistro.objects.all()[:500]:
            ws.append([e.categoria, e.valor, e.cantidad, str(e.fecha)])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=estadisticas.xlsx'
        wb.save(response)
        return response


class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated, EsAdmin]
    queryset = Bitacora.objects.all()


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated, EsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCrearSerializer
        return UsuarioSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        registrar_bitacora(self.request.user.username, 'CREAR_USUARIO', user.username, obtener_ip(self.request))

    def perform_destroy(self, instance):
        username = instance.username
        instance.delete()
        registrar_bitacora(
            self.request.user.username, 'ELIMINAR_USUARIO', username, obtener_ip(self.request),
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response({'error': 'No puede eliminar su propia cuenta.'}, status=400)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            return Response({'error': 'No puede bloquear su propia cuenta.'}, status=400)
        usuario.is_active = False
        usuario.activo_sistema = False
        usuario.save(update_fields=['is_active', 'activo_sistema'])
        registrar_bitacora(
            request.user.username, 'BLOQUEAR_USUARIO', usuario.username, obtener_ip(request),
        )
        return Response(UsuarioSerializer(usuario).data)

    @action(detail=True, methods=['post'])
    def reactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = True
        usuario.activo_sistema = True
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(update_fields=['is_active', 'activo_sistema', 'intentos_fallidos', 'bloqueado_hasta'])
        registrar_bitacora(
            request.user.username, 'REACTIVAR_USUARIO', usuario.username, obtener_ip(request),
        )
        return Response(UsuarioSerializer(usuario).data)

    @action(detail=True, methods=['post'])
    def ver_datos(self, request, pk=None):
        usuario = self.get_object()
        clave_admin = request.data.get('contrasena_admin', '')
        if not clave_admin:
            return Response({'error': 'Debe ingresar su contraseña de administrador.'}, status=400)
        if not request.user.check_password(clave_admin):
            return Response({'error': 'Contraseña de administrador incorrecta.'}, status=403)
        registrar_bitacora(
            request.user.username, 'VER_DATOS_USUARIO', usuario.username, obtener_ip(request),
        )
        return Response(UsuarioDetalleAdminSerializer(usuario).data)


class RegistroDiarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsRegistros()]
        return [IsAuthenticated(), EsLecturaArchivoRegistros()]

    @staticmethod
    def _parse_fecha(fecha_str):
        try:
            f = date.fromisoformat(str(fecha_str)[:10])
        except (TypeError, ValueError):
            raise ValueError('Fecha no válida')
        if f > date.today():
            raise ValueError('La fecha del registro no puede ser futura.')
        return f

    def get(self, request):
        try:
            fecha = self._parse_fecha(request.query_params.get('fecha', str(date.today())))
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        registro, _ = RegistroDiario.objects.get_or_create(fecha=fecha)
        detalles = registro.detalles.select_related('paciente')
        return Response({
            'registro': RegistroDiarioSerializer(registro).data,
            'detalles': RegistroDiarioDetalleSerializer(detalles, many=True).data,
        })

    def post(self, request):
        try:
            fecha = self._parse_fecha(request.data.get('fecha', str(date.today())))
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        paciente_id = request.data.get('paciente_id')
        especialidad = request.data.get('especialidad', '')
        registro, _ = RegistroDiario.objects.get_or_create(fecha=fecha)
        paciente = Paciente.objects.get(pk=paciente_id)
        orden = registro.detalles.count() + 1
        RegistroDiarioDetalle.objects.create(
            registro=registro, paciente=paciente, orden=orden, especialidad=especialidad,
        )
        registro.total_pacientes = registro.detalles.count()
        registro.save()
        return Response({'mensaje': 'Agregado al registro diario'})

    def put(self, request):
        try:
            fecha = self._parse_fecha(request.query_params.get('fecha', str(date.today())))
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        registro = RegistroDiario.objects.filter(fecha=fecha).first()
        if not registro:
            return Response({'error': 'Sin registro'}, status=404)
        detalles = registro.detalles.select_related('paciente')
        return generador_pdf.generar_registro_diario(registro, detalles)


class RespaldoView(APIView):
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        import json
        from django.core import serializers as ser
        datos = {
            'pacientes': json.loads(ser.serialize('json', Paciente.objects.all())),
            'consultas': json.loads(ser.serialize('json', Consulta.objects.all())),
        }
        registrar_bitacora(request.user.username, 'RESPALDO', 'JSON manual', obtener_ip(request))
        return Response({'mensaje': 'Respaldo generado', 'registros': len(datos['pacientes'])})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def catalogos_paciente(request):
    from .catalogos import (
        ESPECIALIDADES, ESTADOS_PACIENTE, ESTADOS_CIVILES, ESTADOS_CITA,
        ESPECIALIDADES_TARDE,
    )
    medicos = Medico.objects.filter(activo=True).order_by('especialidad', 'nombre')
    return Response({
        'especialidades': ESPECIALIDADES,
        'especialidades_tarde': ESPECIALIDADES_TARDE,
        'estados_paciente': ESTADOS_PACIENTE,
        'estados_civiles': ESTADOS_CIVILES,
        'estados_cita': ESTADOS_CITA,
        'medicos': MedicoSerializer(medicos, many=True).data,
        'fecha_hoy': str(date.today()),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_perfil(request):
    return Response({
        'username': request.user.username,
        'rol': request.user.rol,
        'nombre': request.user.get_full_name(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsRegistros])
def busqueda_registros(request):
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response([])
    pacientes = Paciente.objects.filter(
        Q(dpi__icontains=q) |
        Q(numero_expediente__icontains=q) |
        Q(primer_nombre__icontains=q) |
        Q(segundo_nombre__icontains=q) |
        Q(primer_apellido__icontains=q) |
        Q(segundo_apellido__icontains=q)
    )[:30]
    return Response(PacienteSerializer(pacientes, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsArchivo])
def archivo_buscar_citas(request):
    fecha = request.query_params.get('fecha', '').strip()
    especialidad = request.query_params.get('especialidad', '').strip()
    citas = Cita.objects.select_related('paciente', 'medico').all()
    if fecha:
        citas = citas.filter(fecha=fecha)
    if especialidad:
        citas = citas.filter(especialidad=especialidad)
    citas = citas.order_by('fecha', 'hora')[:200]
    return Response(CitaSerializer(citas, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, EsArchivo])
def busqueda_archivo(request):
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({'resultados': []})
    pacientes = Paciente.objects.filter(
        Q(dpi__icontains=q) |
        Q(numero_expediente__icontains=q) |
        Q(primer_nombre__icontains=q) |
        Q(primer_apellido__icontains=q)
    )[:30]
    return Response(PacienteSerializer(pacientes, many=True).data)
