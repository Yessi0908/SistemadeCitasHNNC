import mimetypes
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.conf import settings


def inicio(request):
    return redirect('login_vista')


def login_vista(request):
    return render(request, 'login.html')


def panel(request):
    return render(request, 'panel.html')


def logo_institucional(request):
    if settings.LOGO_RUTA.exists():
        tipo = mimetypes.guess_type(str(settings.LOGO_RUTA))[0] or 'image/jpeg'
        return FileResponse(open(settings.LOGO_RUTA, 'rb'), content_type=tipo)
    raise Http404
