"""
Escaneo de seguridad del Sistema Hospitalario HNNCJ.

Uso (desde la carpeta Demo02):
    python pruebas/escaneo_seguridad.py escaneo_inicial
    python pruebas/escaneo_seguridad.py escaneo_final

Herramientas que combina:
  1. Bandit            -> análisis estático del código Python (SAST).
  2. pip-audit         -> vulnerabilidades conocidas (CVE/PYSEC) en requirements.txt.
  3. check --deploy    -> revisión de configuración de producción de Django.
  4. Pruebas HTTP      -> ataques simulados contra la API con DEBUG=False.
  5. Análisis frontend -> datos insertados en innerHTML sin escapar (XSS).

Cada control tiene severidad (Alta=10, Media=5, Baja=2 puntos).
Puntuación = puntos de controles aprobados / puntos totales * 100.
Los resultados se guardan en pruebas/<carpeta>/.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PESOS = {'Alta': 10, 'Media': 5, 'Baja': 2}
PY = sys.executable

CONTROLES_DEPLOY = [
    ('security.W004', 'HSTS configurado (SECURE_HSTS_SECONDS)', 'Media', 'Confidencialidad'),
    ('security.W008', 'Redirección obligatoria a HTTPS (SECURE_SSL_REDIRECT)', 'Media', 'Confidencialidad'),
    ('security.W009', 'SECRET_KEY larga y aleatoria', 'Alta', 'Integridad'),
    ('security.W012', 'Cookie de sesión solo por HTTPS', 'Media', 'Confidencialidad'),
    ('security.W016', 'Cookie CSRF solo por HTTPS', 'Media', 'Integridad'),
    ('security.W018', 'DEBUG desactivado en producción', 'Alta', 'Confidencialidad'),
    ('security.W019', 'X-Frame-Options en DENY', 'Baja', 'Integridad'),
    ('security.W020', 'ALLOWED_HOSTS definido', 'Media', 'Integridad'),
]


def ejecutar(cmd, env_extra=None):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env.update(env_extra or {})
    r = subprocess.run(cmd, cwd=BASE, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------------------
# 1-3. Herramientas externas
# ---------------------------------------------------------------------------

def escaneo_bandit(salida):
    _, out, err = ejecutar([PY, '-m', 'bandit', '-r', 'app', 'config', '-x', 'app/migrations,app/tests', '-f', 'json', '-q'])
    (salida / 'bandit.json').write_text(out or err, encoding='utf-8')
    try:
        hallazgos = json.loads(out).get('results', [])
    except json.JSONDecodeError:
        hallazgos = []
    controles = []
    for sev_bandit, sev in (('HIGH', 'Alta'), ('MEDIUM', 'Media'), ('LOW', 'Baja')):
        lista = [h for h in hallazgos if h['issue_severity'] == sev_bandit]
        controles.append({
            'id': f'bandit_{sev_bandit.lower()}',
            'herramienta': 'Bandit',
            'titulo': f'Código Python sin hallazgos de severidad {sev.lower()}',
            'severidad': sev,
            'pilar': 'Integridad',
            'aprobado': not lista,
            'evidencia': '; '.join(
                f"{h['test_id']} {h['issue_text']} ({Path(h['filename']).as_posix()}:{h['line_number']})" for h in lista
            ) or 'Sin hallazgos',
        })
    return controles


def escaneo_pip_audit(salida):
    _, out, err = ejecutar([PY, '-m', 'pip_audit', '-r', 'requirements.txt', '-f', 'json', '--progress-spinner', 'off'])
    (salida / 'pip_audit.json').write_text(out or err, encoding='utf-8')
    vulnerables = {}
    try:
        for dep in json.loads(out).get('dependencies', []):
            for v in dep.get('vulns', []):
                vulnerables.setdefault(f"{dep['name']} {dep['version']}", set()).add(
                    f"{v['id']} (corregido en {', '.join(v.get('fix_versions') or ['?'])})"
                )
    except json.JSONDecodeError:
        pass
    return [{
        'id': 'dependencias_sin_cve',
        'herramienta': 'pip-audit',
        'titulo': 'Dependencias sin vulnerabilidades conocidas',
        'severidad': 'Alta',
        'pilar': 'Integridad',
        'aprobado': not vulnerables,
        'evidencia': '; '.join(f"{k}: {', '.join(sorted(v))}" for k, v in vulnerables.items()) or 'Sin vulnerabilidades',
    }]


def escaneo_deploy(salida):
    _, out, err = ejecutar(
        [PY, 'manage.py', 'check', '--deploy'],
        {'DEBUG': 'False', 'ALLOWED_HOSTS': 'hospital.local,localhost,127.0.0.1'},
    )
    texto = (out or '') + (err or '')
    (salida / 'django_check_deploy.txt').write_text(texto, encoding='utf-8')
    controles = []
    for codigo, titulo, sev, pilar in CONTROLES_DEPLOY:
        linea = next((l.strip() for l in texto.splitlines() if f'({codigo})' in l), '')
        controles.append({
            'id': codigo,
            'herramienta': 'Django check --deploy',
            'titulo': titulo,
            'severidad': sev,
            'pilar': pilar,
            'aprobado': not linea,
            'evidencia': linea[:220] or 'Sin advertencia',
        })
    return controles


# ---------------------------------------------------------------------------
# 4. Análisis estático del frontend (XSS por innerHTML)
# ---------------------------------------------------------------------------

PATRON_DATO = re.compile(r'\b(p|c|d|m|u|b|n|row|data|e)(\.(?!id\b|length\b)\w+|\[c\])')
# Funciones de panel.js que reciben listas y escapan cada celda internamente (sus líneas también se analizan).
HELPERS_QUE_ESCAPAN = ('tablaCitasHtml(', 'tablaDesdeLista(', 'htmlCitasVAS(')


def analizar_frontend():
    js = (BASE / 'static' / 'js' / 'panel.js').read_text(encoding='utf-8')
    inseguros = []
    for num, linea in enumerate(js.splitlines(), 1):
        if not re.search(r'innerHTML\s*=|\bh(tml)?\s*\+?=', linea):
            continue
        for m in PATRON_DATO.finditer(linea):
            tramo = linea[:m.start()].rsplit('+', 1)[-1]
            if 'esc(' not in tramo and not tramo.rstrip().endswith(HELPERS_QUE_ESCAPAN):
                inseguros.append(f'panel.js:{num} {m.group(0)}')
    return [{
        'id': 'xss_frontend',
        'herramienta': 'Análisis estático JS',
        'titulo': 'Datos de la API se escapan antes de insertarse con innerHTML',
        'severidad': 'Alta',
        'pilar': 'Confidencialidad',
        'aprobado': not inseguros,
        'evidencia': (f'{len(inseguros)} inserciones sin escapar, p. ej. ' + ', '.join(inseguros[:6])) if inseguros else 'Todas las inserciones usan esc()',
    }]


# ---------------------------------------------------------------------------
# 5. Pruebas HTTP dinámicas (se ejecutan en un subproceso con DEBUG=False)
# ---------------------------------------------------------------------------

def escaneo_dinamico_subproceso(salida):
    _, out, err = ejecutar(
        [PY, str(Path(__file__).resolve()), '--dinamico'],
        {'DEBUG': 'False', 'USE_SQLITE': 'True', 'ALLOWED_HOSTS': 'hospital.local,localhost,127.0.0.1,testserver'},
    )
    (salida / 'pruebas_http.log').write_text(err or '', encoding='utf-8')
    marca = out.rfind('@@JSON@@')
    if marca == -1:
        raise SystemExit('El escaneo dinámico falló:\n' + (err or out))
    return json.loads(out[marca + len('@@JSON@@'):])


def escaneo_dinamico():
    sys.path.insert(0, str(BASE))
    os.chdir(BASE)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()

    import logging
    logging.disable(logging.CRITICAL)

    from datetime import date, timedelta
    from django.contrib.auth import get_user_model
    from django.core.cache import cache
    from django.test.runner import DiscoverRunner
    from django.test.utils import setup_test_environment
    from rest_framework.test import APIClient
    from app.models import Bitacora, Paciente, Rol

    Usuario = get_user_model()
    CLAVE = 'Hnncj#Escaneo2026'

    setup_test_environment()
    runner = DiscoverRunner(verbosity=0)
    bases = runner.setup_databases()

    def usuario(nombre, rol, **extra):
        u = Usuario(username=nombre, rol=rol, **extra)
        u.set_password(CLAVE)
        u.save()
        return u

    def cliente(user=None, ip='198.51.100.10'):
        c = APIClient(raise_request_exception=False, REMOTE_ADDR=ip)
        if user:
            c.force_authenticate(user)
        return c

    def login(c, nombre, clave, **extra):
        return c.post('/api/auth/login/', {'username': nombre, 'password': clave}, format='json', secure=True, **extra)

    admin = usuario('esc_admin', Rol.ADMIN, is_staff=True, is_superuser=True)
    archivo = usuario('esc_archivo', Rol.ARCHIVO)
    estad = usuario('esc_estadistica', Rol.ESTADISTICA)
    registros = usuario('esc_registros', Rol.REGISTROS)
    usuario('esc_inactivo', Rol.REGISTROS, is_active=False, activo_sistema=False)

    pruebas = []

    def prueba(titulo, severidad, pilar):
        def deco(fn):
            pruebas.append((fn, titulo, severidad, pilar))
            return fn
        return deco

    @prueba('La API exige autenticación (anónimo -> 401)', 'Alta', 'Confidencialidad')
    def p_auth():
        r = cliente().get('/api/pacientes/', secure=True)
        return r.status_code == 401, f'GET /api/pacientes/ anónimo -> {r.status_code}'

    @prueba('Rol archivo no puede crear pacientes (RBAC)', 'Alta', 'Integridad')
    def p_rbac1():
        r = cliente(archivo).post('/api/pacientes/', {'primer_apellido': 'X', 'primer_nombre': 'Y', 'dpi': '9'}, format='json', secure=True)
        return r.status_code == 403, f'POST /api/pacientes/ como archivo -> {r.status_code}'

    @prueba('Solo el administrador gestiona usuarios (RBAC)', 'Alta', 'Confidencialidad')
    def p_rbac2():
        r = cliente(estad).get('/api/usuarios/', secure=True)
        return r.status_code == 403, f'GET /api/usuarios/ como estadistica -> {r.status_code}'

    @prueba('Contraseñas almacenadas con hash bcrypt', 'Alta', 'Confidencialidad')
    def p_hash():
        h = Usuario.objects.get(pk=admin.pk).password
        return h.startswith('bcrypt_sha256$'), f'Algoritmo: {h.split("$")[0]}'

    @prueba('Bloqueo de cuenta tras intentos fallidos', 'Media', 'Disponibilidad')
    def p_bloqueo():
        u = usuario('esc_bloqueo', Rol.ARCHIVO)
        for i in range(5):
            login(cliente(ip=f'198.51.100.{50 + i}'), u.username, 'incorrecta')
        r = login(cliente(ip='198.51.100.60'), u.username, CLAVE)
        return r.status_code == 403, f'Login correcto tras 5 fallos -> {r.status_code}'

    @prueba('Cierre de sesión invalida el refresh token', 'Media', 'Confidencialidad')
    def p_logout():
        c = cliente()
        tokens = login(c, registros.username, CLAVE).json()
        c.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens.get('access', ''))
        c.post('/api/auth/logout/', {'refresh': tokens.get('refresh')}, format='json', secure=True)
        r = cliente().post('/api/auth/token/refresh/', {'refresh': tokens.get('refresh')}, format='json', secure=True)
        return r.status_code == 401, f'Refresh tras logout -> {r.status_code}'

    @prueba('Errores sin trazas internas (sin modo DEBUG)', 'Media', 'Confidencialidad')
    def p_debug():
        r = cliente().get('/ruta-que-no-existe/', secure=True)
        filtra = b'Traceback' in r.content or b'URLconf' in r.content
        return r.status_code == 404 and not filtra, f'404 con información interna: {"sí" if filtra else "no"}'

    @prueba('La API rechaza HTML/JavaScript en datos de pacientes (XSS almacenado)', 'Alta', 'Integridad')
    def p_xss():
        r = cliente(admin).post('/api/pacientes/', {
            'primer_apellido': 'Prueba', 'primer_nombre': '<img src=x onerror=alert(document.cookie)>',
            'dpi': '3000111220101',
        }, format='json', secure=True)
        return r.status_code == 400, f'POST paciente con <img onerror> -> {r.status_code}'

    @prueba('La contraseña de referencia no se guarda en texto plano', 'Alta', 'Confidencialidad')
    def p_plano():
        clave = 'Referencia#Escaneo91'
        cliente(admin).post('/api/usuarios/', {'username': 'esc_nuevo', 'password': clave, 'rol': 'archivo'}, format='json', secure=True)
        u = Usuario.objects.filter(username='esc_nuevo').first()
        if not u:
            return False, 'No se pudo crear el usuario de prueba'
        return clave not in (u.clave_referencia or ''), f'clave_referencia en BD: {(u.clave_referencia or "")[:18]}…'

    @prueba('Se rechazan contraseñas débiles o comunes', 'Media', 'Confidencialidad')
    def p_politica():
        r = cliente(admin).post('/api/usuarios/', {'username': 'esc_debil', 'password': '12345678', 'rol': 'archivo'}, format='json', secure=True)
        return r.status_code == 400, f'Crear usuario con clave "12345678" -> {r.status_code}'

    @prueba('El login no revela si una cuenta existe o está inactiva', 'Media', 'Confidencialidad')
    def p_enum():
        a = login(cliente(ip='198.51.100.70'), 'esc_inactivo', 'incorrecta')
        b = login(cliente(ip='198.51.100.71'), 'usuario_que_no_existe', 'incorrecta')
        igual = a.status_code == b.status_code and a.json() == b.json()
        return igual, f'Inactivo -> {a.status_code} {a.json()} | Inexistente -> {b.status_code} {b.json()}'

    @prueba('Límite de intentos de login por dirección IP', 'Media', 'Disponibilidad')
    def p_throttle():
        codigos = [login(cliente(ip='198.51.100.80'), f'falso{i}', 'x').status_code for i in range(15)]
        return 429 in codigos, f'15 intentos desde una IP -> códigos {sorted(set(codigos))}'

    @prueba('La bitácora no acepta IP falsificada con X-Forwarded-For', 'Media', 'Integridad')
    def p_xff():
        login(cliente(ip='198.51.100.90'), 'esc_xff', 'x', HTTP_X_FORWARDED_FOR='203.0.113.66')
        ultima = Bitacora.objects.filter(usuario='esc_xff').first()
        ip = ultima.ip if ultima else None
        return ip != '203.0.113.66', f'IP registrada: {ip}'

    @prueba('Documentación de la API no es pública', 'Media', 'Confidencialidad')
    def p_docs():
        r = cliente().get('/api/schema/', secure=True)
        return r.status_code in (401, 403, 404), f'GET /api/schema/ anónimo -> {r.status_code}'

    @prueba('Peticiones HTTP se redirigen a HTTPS', 'Media', 'Confidencialidad')
    def p_https():
        r = cliente().get('/login/')
        destino = r.get('Location', '')
        return r.status_code == 301 and destino.startswith('https://'), f'GET http://…/login/ -> {r.status_code} {destino}'

    @prueba('Entrada inválida no provoca error 500 (registro diario)', 'Media', 'Disponibilidad')
    def p_500():
        r = cliente(registros).post('/api/registro-diario/', {'fecha': str(date.today()), 'paciente_id': 999999}, format='json', secure=True)
        return r.status_code in (400, 404), f'POST registro diario con paciente inexistente -> {r.status_code}'

    cabeceras = [
        ('Strict-Transport-Security', 'Cabecera HSTS', 'Media'),
        ('Content-Security-Policy', 'Cabecera Content-Security-Policy', 'Media'),
        ('X-Content-Type-Options', 'Cabecera X-Content-Type-Options', 'Baja'),
        ('X-Frame-Options', 'Cabecera X-Frame-Options (anti clickjacking)', 'Baja'),
        ('Referrer-Policy', 'Cabecera Referrer-Policy', 'Baja'),
        ('Cross-Origin-Opener-Policy', 'Cabecera Cross-Origin-Opener-Policy', 'Baja'),
    ]
    for nombre, titulo, sev in cabeceras:
        def p_cab(nombre=nombre):
            r = cliente().get('/login/', secure=True)
            valor = r.get(nombre)
            return bool(valor), f'{nombre}: {valor or "(ausente)"}'
        prueba(titulo, sev, 'Confidencialidad')(p_cab)

    resultados = []
    try:
        for fn, titulo, sev, pilar in pruebas:
            cache.clear()
            try:
                ok, evidencia = fn()
            except Exception as exc:
                ok, evidencia = False, f'Excepción: {type(exc).__name__}: {exc}'
            resultados.append({
                'id': fn.__name__, 'herramienta': 'Pruebas HTTP', 'titulo': titulo,
                'severidad': sev, 'pilar': pilar, 'aprobado': bool(ok), 'evidencia': str(evidencia)[:300],
            })
    finally:
        runner.teardown_databases(bases)
    print('@@JSON@@' + json.dumps(resultados, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def generar_reporte(carpeta):
    salida = BASE / 'pruebas' / carpeta
    salida.mkdir(parents=True, exist_ok=True)
    print(f'Escaneando… resultados en {salida}')

    controles = []
    for nombre, paso in (
        ('Bandit', lambda: escaneo_bandit(salida)),
        ('pip-audit', lambda: escaneo_pip_audit(salida)),
        ('check --deploy', lambda: escaneo_deploy(salida)),
        ('Frontend', analizar_frontend),
        ('Pruebas HTTP', lambda: escaneo_dinamico_subproceso(salida)),
    ):
        print(f'  - {nombre}…')
        controles += paso()

    total = sum(PESOS[c['severidad']] for c in controles)
    obtenido = sum(PESOS[c['severidad']] for c in controles if c['aprobado'])
    puntuacion = round(obtenido / total * 100, 1)
    fallidos = [c for c in controles if not c['aprobado']]

    lineas = [
        '=' * 78,
        f' REPORTE DE ESCANEO DE SEGURIDAD — {carpeta}',
        f' Sistema Hospitalario HNNCJ — {datetime.now():%Y-%m-%d %H:%M}',
        '=' * 78,
        f' PUNTUACIÓN: {puntuacion} / 100   ({obtenido} de {total} puntos)',
        f' Controles aprobados: {len(controles) - len(fallidos)} de {len(controles)}',
        ' Hallazgos abiertos por severidad: ' + ', '.join(
            f"{s}={sum(1 for c in fallidos if c['severidad'] == s)}" for s in PESOS
        ),
        '',
    ]
    for pilar in ('Confidencialidad', 'Integridad', 'Disponibilidad'):
        del_pilar = [c for c in controles if c['pilar'] == pilar]
        ok = sum(1 for c in del_pilar if c['aprobado'])
        lineas.append(f' {pilar}: {ok}/{len(del_pilar)} controles aprobados')
    lineas += ['', '-' * 78]
    for c in controles:
        estado = 'APROBADO ' if c['aprobado'] else 'FALLA    '
        lineas.append(f"[{estado}] [{c['severidad']:<5}] {c['herramienta']}: {c['titulo']}")
        lineas.append(f"            Evidencia: {c['evidencia']}")
    lineas.append('=' * 78)

    texto = '\n'.join(lineas)
    (salida / 'reporte.txt').write_text(texto, encoding='utf-8')
    (salida / 'reporte.json').write_text(json.dumps({
        'fecha': datetime.now().isoformat(timespec='seconds'),
        'puntuacion': puntuacion, 'controles': controles,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--dinamico':
        escaneo_dinamico()
    else:
        generar_reporte(sys.argv[1] if len(sys.argv) > 1 else 'escaneo')
