from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_medico_cita_medico_estados'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='clave_referencia',
            field=models.CharField(
                blank=True,
                help_text='Referencia interna de contraseña visible solo al administrador autenticado.',
                max_length=128,
            ),
        ),
    ]
