import django.db.models.deletion
from django.db import migrations, models


def migrar_estado_programada(apps, schema_editor):
    Cita = apps.get_model('app', 'Cita')
    Cita.objects.filter(estado='Programada').update(estado='Confirmada')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_paciente_catalogos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Medico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('especialidad', models.CharField(max_length=100)),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Médico',
                'verbose_name_plural': 'Médicos',
                'ordering': ['especialidad', 'nombre'],
            },
        ),
        migrations.AddField(
            model_name='cita',
            name='medico',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='citas', to='app.medico'),
        ),
        migrations.RunPython(migrar_estado_programada, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='cita',
            name='estado',
            field=models.CharField(choices=[('Confirmada', 'Confirmada'), ('Cancelada', 'Cancelada'), ('Atendida', 'Atendida')], default='Confirmada', max_length=20),
        ),
    ]
