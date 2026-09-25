

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tarefas', '0002_alter_instanciatarefa_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='SugestaoTarefa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icone', models.CharField(default='✨', max_length=8)),
                ('titulo', models.CharField(max_length=120, unique=True)),
                ('descricao', models.TextField(blank=True)),
                ('categoria', models.CharField(choices=[('AUTOCUIDADO', 'Autocuidado'), ('ORGANIZACAO', 'Organização'), ('ESTUDOS', 'Estudos'), ('CASA', 'Casa'), ('AUTONOMIA', 'Autonomia'), ('COLABORACAO', 'Colaboração')], max_length=20)),
                ('idade_minima', models.PositiveSmallIntegerField(default=3)),
                ('idade_maxima', models.PositiveSmallIntegerField(default=17)),
                ('pontos_sugeridos', models.PositiveSmallIntegerField(default=5)),
                ('frequencia_sugerida', models.CharField(choices=[('DIARIA', 'Diária'), ('SEMANAL', 'Semanal')], default='DIARIA', max_length=10)),
                ('dias_semana', models.CharField(blank=True, default='', max_length=20)),
                ('ativa', models.BooleanField(default=True)),
                ('ordem', models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                'verbose_name': 'Sugestão de tarefa',
                'verbose_name_plural': 'Sugestões de tarefas',
                'ordering': ('ordem', 'titulo'),
            },
        ),
    ]
