from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

from app.models import Rol

Usuario = get_user_model()

# Contraseñas SOLO desde variables de entorno (.env). Nunca hardcodear en el código.
USUARIOS = [
    ('archivo', 'INIT_PASS_ARCHIVO', Rol.ARCHIVO),
    ('registros', 'INIT_PASS_REGISTROS', Rol.REGISTROS),
    ('estadistica', 'INIT_PASS_ESTADISTICA', Rol.ESTADISTICA),
    ('juridico', 'INIT_PASS_JURIDICO', Rol.JURIDICO),
    ('Jramirez', 'INIT_PASS_ADMIN', Rol.ADMIN),
]


class Command(BaseCommand):
    help = 'Crea usuarios iniciales del hospital (contraseñas desde .env)'

    def handle(self, *args, **options):
        faltantes = []
        pares = []
        for username, env_key, rol in USUARIOS:
            password = os.getenv(env_key, '').strip()
            if not password:
                faltantes.append(env_key)
            else:
                pares.append((username, password, rol))

        if faltantes:
            self.stderr.write(self.style.ERROR(
                'Faltan contraseñas en .env: ' + ', '.join(faltantes)
            ))
            self.stderr.write(
                'Copie .env.example a .env y defina INIT_PASS_* antes de ejecutar inicializar.'
            )
            return

        for username, password, rol in pares:
            user, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={'rol': rol, 'is_staff': rol == Rol.ADMIN},
            )
            user.rol = rol
            user.set_password(password)
            user.clave_referencia = password
            user.activo_sistema = True
            user.is_active = True
            if rol == Rol.ADMIN:
                user.is_superuser = True
                user.is_staff = True
            user.save()
            estado = 'creado' if creado else 'actualizado'
            self.stdout.write(f'  {username} ({rol}) — {estado}')

        Usuario.objects.filter(username='admin').update(
            is_active=False, activo_sistema=False,
        )

        self.stdout.write(self.style.SUCCESS('Usuarios listos.'))
