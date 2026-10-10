from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csp import csp_override
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from app import vistas_web

docs_csp = csp_override(settings.CSP_DOCUMENTACION_API)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Documentación de la API: solo administradores con sesión iniciada en /admin/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', docs_csp(SpectacularSwaggerView.as_view(url_name='schema')), name='swagger-ui'),
    path('api/redoc/', docs_csp(SpectacularRedocView.as_view(url_name='schema')), name='redoc'),
    path('api/', include('app.urls')),
    path('', vistas_web.inicio),
    path('login/', vistas_web.login_vista, name='login_vista'),
    path('panel/', vistas_web.panel),
    path('logo/', vistas_web.logo_institucional),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
