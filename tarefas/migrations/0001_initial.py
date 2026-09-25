

import django.db.models.deletion
import tarefas.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('usuarios', '0003_alter_perfilcrianca_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MoldeTarefa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('descricao', models.TextField(blank=True)),
                ('pontos_base', models.PositiveSmallIntegerField(default=10)),
                ('frequencia', models.CharField(choices=[('DIARIA', 'Diária'), ('SEMANAL', 'Semanal')], default='DIARIA', max_length=10)),
                ('dias_semana', models.CharField(blank=True, default='', help_text='Dias de 0 a 6 separados por vírgula.', max_length=20)),
                ('ativa', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='moldes_criados', to=settings.AUTH_USER_MODEL)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moldes_tarefas', to='usuarios.perfilcrianca')),
                ('familia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moldes_tarefas', to='usuarios.familia')),
            ],
            options={
                'verbose_name': 'Molde de tarefa',
                'verbose_name_plural': 'Moldes de tarefas',
                'ordering': ('crianca__nome', 'titulo'),
            },
        ),
        migrations.CreateModel(
            name='InstanciaTarefa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origem', models.CharField(choices=[('MOLDE', 'Molde'), ('BONUS', 'Bônus')], default='MOLDE', max_length=10)),
                ('titulo', models.CharField(max_length=120)),
                ('descricao', models.TextField(blank=True)),
                ('pontos_base', models.PositiveSmallIntegerField(default=10)),
                ('data_referencia', models.DateField(db_index=True)),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('REVISAO', 'Aguardando revisão'), ('APROVADA', 'Aprovada'), ('REJEITADA', 'Rejeitada')], db_index=True, default='PENDENTE', max_length=12)),
                ('foto', models.ImageField(blank=True, null=True, upload_to=tarefas.models.caminho_comprovante)),
                ('enviada_em', models.DateTimeField(blank=True, null=True)),
                ('feedback_tutor', models.TextField(blank=True)),
                ('pontos_concedidos', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('revisada_em', models.DateTimeField(blank=True, null=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('criada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tarefas_lancadas', to=settings.AUTH_USER_MODEL)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tarefas', to='usuarios.perfilcrianca')),
                ('familia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tarefas', to='usuarios.familia')),
                ('revisada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tarefas_revisadas', to=settings.AUTH_USER_MODEL)),
                ('molde', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instancias', to='tarefas.moldetarefa')),
            ],
            options={
                'verbose_name': 'Tarefa',
                'verbose_name_plural': 'Tarefas',
                'ordering': ('-data_referencia', 'status', 'criada_em'),
                'constraints': [models.UniqueConstraint(condition=models.Q(('molde__isnull', False)), fields=('molde', 'data_referencia'), name='tarefa_unica_por_molde_data')],
            },
        ),
    ]
