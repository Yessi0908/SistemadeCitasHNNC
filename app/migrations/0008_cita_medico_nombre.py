from django.db import migrations, models


def copiar_nombre_medico(apps, schema_editor):
    Cita = apps.get_model('app', 'Cita')
    for cita in Cita.objects.select_related('medico').all():
        if cita.medico and not cita.medico_nombre:
            cita.medico_nombre = cita.medico.nombre
            cita.save(update_fields=['medico_nombre'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_especialidades_ekg_videocirugia'),
    ]

    operations = [
        migrations.AddField(
            model_name='cita',
            name='medico_nombre',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.RunPython(copiar_nombre_medico, migrations.RunPython.noop),
    ]
