from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_cita_medico_nombre'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotaVAS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField()),
                ('lista', models.BooleanField(default=False)),
                ('creado_por', models.CharField(blank=True, max_length=150)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('confirmada_por', models.CharField(blank=True, max_length=150)),
                ('confirmada', models.DateTimeField(blank=True, null=True)),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notas_vas',
                    to='app.paciente',
                )),
            ],
            options={
                'verbose_name': 'Nota jurídica VAS',
                'verbose_name_plural': 'Notas jurídicas VAS',
                'ordering': ['-creado'],
            },
        ),
    ]
