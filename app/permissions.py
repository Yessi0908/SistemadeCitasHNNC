from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Rol


class EsRol(BasePermission):
    roles_permitidos = []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.rol in self.roles_permitidos


class EsAdmin(EsRol):
    roles_permitidos = [Rol.ADMIN]


class EsArchivo(EsRol):
    roles_permitidos = [Rol.ARCHIVO, Rol.ADMIN]


class EsRegistros(EsRol):
    roles_permitidos = [Rol.REGISTROS, Rol.ADMIN]


class EsEstadistica(EsRol):
    roles_permitidos = [Rol.ESTADISTICA, Rol.ADMIN]


class EsJuridico(EsRol):
    roles_permitidos = [Rol.JURIDICO, Rol.ADMIN]


class EsLecturaArchivoRegistros(BasePermission):
    """Consulta para archivo, registros y administrador."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.rol in (Rol.ARCHIVO, Rol.REGISTROS, Rol.ADMIN)


class SoloLecturaArchivo(BasePermission):
    """Archivo solo consulta; admin y registros pueden escribir."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.rol == Rol.ARCHIVO:
            return request.method in SAFE_METHODS
        if request.user.rol in (Rol.REGISTROS, Rol.ADMIN):
            return True
        if request.user.rol == Rol.ESTADISTICA:
            return request.method in SAFE_METHODS
        return False
