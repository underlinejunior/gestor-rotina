

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tarefas', '0002_alter_instanciatarefa_status'),
        ('usuarios', '0003_alter_perfilcrianca_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MovimentoPontos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('APROVACAO', 'Aprovação de tarefa'), ('AJUSTE', 'Ajuste manual')], default='APROVACAO', max_length=20)),
                ('pontos', models.IntegerField()),
                ('saldo_apos', models.PositiveIntegerField(default=0)),
                ('nivel_antes', models.PositiveSmallIntegerField(default=1)),
                ('nivel_depois', models.PositiveSmallIntegerField(default=1)),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentos_pontos', to='usuarios.perfilcrianca')),
                ('registrado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_pontos_registrados', to=settings.AUTH_USER_MODEL)),
                ('tarefa', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimento_pontos', to='tarefas.instanciatarefa')),
            ],
            options={
                'verbose_name': 'Movimento de pontos',
                'verbose_name_plural': 'Movimentos de pontos',
                'ordering': ('-criado_em',),
            },
        ),
    ]
