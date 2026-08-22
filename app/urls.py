from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register('pacientes', views.PacienteViewSet)
router.register('consultas', views.ConsultaViewSet)
router.register('citas', views.CitaViewSet)
router.register('vas', views.VASViewSet)
router.register('estadistica', views.EstadisticaViewSet)
router.register('bitacora', views.BitacoraViewSet)
router.register('usuarios', views.UsuarioViewSet)
router.register('medicos', views.MedicoViewSet)

urlpatterns = [
    path('auth/login/', views.LoginView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/perfil/', views.mi_perfil),
    path('catalogos/paciente/', views.catalogos_paciente),
    path('registros/buscar/', views.busqueda_registros),
    path('archivo/buscar/', views.busqueda_archivo),
    path('archivo/citas/', views.archivo_buscar_citas),
    path('registro-diario/', views.RegistroDiarioView.as_view()),
    path('respaldo/', views.RespaldoView.as_view()),
    path('', include(router.urls)),
]
