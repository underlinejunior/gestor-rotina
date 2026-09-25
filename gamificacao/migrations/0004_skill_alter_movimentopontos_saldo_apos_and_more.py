

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamificacao', '0003_notificacaosistema_chave_notificacaosistema_tarefa_and_more'),
        ('tarefas', '0003_sugestaotarefa'),
        ('usuarios', '0005_alter_perfilcrianca_saldo_pontos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('icone', models.CharField(default='✨', max_length=8)),
                ('descricao', models.CharField(blank=True, max_length=220)),
                ('ativa', models.BooleanField(default=True)),
                ('ordem', models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                'verbose_name': 'Habilidade',
                'verbose_name_plural': 'Habilidades',
                'ordering': ('ordem', 'nome'),
            },
        ),
        migrations.AlterField(
            model_name='movimentopontos',
            name='saldo_apos',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='movimentopontos',
            name='tipo',
            field=models.CharField(choices=[('APROVACAO', 'Aprovação de tarefa'), ('PENALIDADE', 'Tarefa não realizada'), ('AJUSTE', 'Ajuste manual')], default='APROVACAO', max_length=20),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='chave',
            field=models.CharField(blank=True, db_index=True, default='', max_length=180),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='tipo',
            field=models.CharField(choices=[('NIVEL_AVATAR', 'Mudança de nível do avatar'), ('NIVEL_HABILIDADE', 'Mudança de nível de habilidade'), ('TAREFA_NAO_REALIZADA', 'Tarefa não realizada'), ('RESUMO_DIARIO', 'Resumo diário'), ('RESUMO_SEMANAL', 'Resumo semanal')], default='NIVEL_AVATAR', max_length=30),
        ),
        migrations.AddField(
            model_name='notificacaosistema',
            name='skill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notificacoes_sistema', to='gamificacao.skill'),
        ),
        migrations.CreateModel(
            name='ProgressoSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xp_total', models.PositiveIntegerField(default=0)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progressos_skills', to='usuarios.perfilcrianca')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='progressos', to='gamificacao.skill')),
            ],
            options={
                'verbose_name': 'Progresso de habilidade',
                'verbose_name_plural': 'Progressos de habilidades',
                'constraints': [models.UniqueConstraint(fields=('crianca', 'skill'), name='progresso_skill_crianca_unico')],
            },
        ),
        migrations.CreateModel(
            name='MovimentoSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xp', models.PositiveSmallIntegerField()),
                ('nivel_antes', models.PositiveSmallIntegerField(default=1)),
                ('nivel_depois', models.PositiveSmallIntegerField(default=1)),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentos_skills', to='usuarios.perfilcrianca')),
                ('tarefa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_skills', to='tarefas.instanciatarefa')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimentos', to='gamificacao.skill')),
            ],
            options={
                'verbose_name': 'Movimento de habilidade',
                'verbose_name_plural': 'Movimentos de habilidades',
                'ordering': ('-criado_em',),
                'constraints': [models.UniqueConstraint(condition=models.Q(('tarefa__isnull', False)), fields=('tarefa', 'skill'), name='movimento_skill_tarefa_unico')],
            },
        ),
        migrations.CreateModel(
            name='MoldeTarefaSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('impacto', models.PositiveSmallIntegerField(choices=[(1, 'Leve'), (2, 'Médio'), (3, 'Forte')], default=2)),
                ('molde', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills_associadas', to='tarefas.moldetarefa')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='moldes_associados', to='gamificacao.skill')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('molde', 'skill'), name='molde_skill_unica')],
            },
        ),
        migrations.CreateModel(
            name='InstanciaTarefaSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_snapshot', models.CharField(max_length=80)),
                ('icone_snapshot', models.CharField(default='✨', max_length=8)),
                ('impacto', models.PositiveSmallIntegerField(choices=[(1, 'Leve'), (2, 'Médio'), (3, 'Forte')])),
                ('xp_planejado', models.PositiveSmallIntegerField(default=0)),
                ('tarefa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills_snapshot', to='tarefas.instanciatarefa')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instancias_associadas', to='gamificacao.skill')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('tarefa', 'skill'), name='instancia_skill_unica')],
            },
        ),
        migrations.CreateModel(
            name='SugestaoTarefaSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('impacto', models.PositiveSmallIntegerField(choices=[(1, 'Leve'), (2, 'Médio'), (3, 'Forte')], default=2)),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sugestoes_associadas', to='gamificacao.skill')),
                ('sugestao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills_associadas', to='tarefas.sugestaotarefa')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('sugestao', 'skill'), name='sugestao_skill_unica')],
            },
        ),
    ]
