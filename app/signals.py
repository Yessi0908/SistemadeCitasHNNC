from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Paciente
from .utils import calcular_edad


@receiver(pre_save, sender=Paciente)
def actualizar_edad(sender, instance, **kwargs):
    if instance.fecha_nacimiento:
        a, m, d = calcular_edad(instance.fecha_nacimiento)
        instance.edad_anios, instance.edad_meses, instance.edad_dias = a, m, d
