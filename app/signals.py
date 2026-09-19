from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from .models import Paciente, NotaVAS
from .utils import calcular_edad


@receiver(pre_save, sender=Paciente)
def actualizar_edad(sender, instance, **kwargs):
    if instance.fecha_nacimiento:
        a, m, d = calcular_edad(instance.fecha_nacimiento)
        instance.edad_anios, instance.edad_meses, instance.edad_dias = a, m, d


@receiver(pre_save, sender=NotaVAS)
def bloquear_nota_vas_confirmada(sender, instance, **kwargs):
    if not instance.pk:
        return
    anterior = sender.objects.filter(pk=instance.pk).first()
    if anterior and anterior.lista:
        raise ValidationError(
            'Esta nota jurídica ya está confirmada y no se puede modificar, ni siquiera el administrador.'
        )


@receiver(pre_delete, sender=NotaVAS)
def bloquear_borrado_nota_vas_confirmada(sender, instance, **kwargs):
    if instance.lista:
        raise ValidationError(
            'Esta nota jurídica ya está confirmada y no se puede eliminar, ni siquiera el administrador.'
        )
