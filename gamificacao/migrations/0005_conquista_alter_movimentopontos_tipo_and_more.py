

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamificacao', '0004_skill_alter_movimentopontos_saldo_apos_and_more'),
        ('usuarios', '0006_perfilcrianca_pontos_experiencia_convitetutor'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conquista',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.CharField(max_length=220)),
                ('icone', models.CharField(default='🏅', max_length=8)),
                ('ordem', models.PositiveSmallIntegerField(default=100)),
                ('ativa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Conquista',
                'verbose_name_plural': 'Conquistas',
                'ordering': ('ordem', 'nome'),
            },
        ),
        migrations.AlterField(
            model_name='movimentopontos',
            name='tipo',
            field=models.CharField(choices=[('APROVACAO', 'Aprovação de tarefa'), ('PENALIDADE', 'Tarefa não realizada'), ('RESGATE', 'Resgate de recompensa'), ('AJUSTE', 'Ajuste manual')], default='APROVACAO', max_length=20),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='tipo',
            field=models.CharField(choices=[('NIVEL_AVATAR', 'Mudança de nível do avatar'), ('NIVEL_HABILIDADE', 'Mudança de nível de habilidade'), ('CONQUISTA', 'Conquista desbloqueada'), ('RECOMPENSA', 'Recompensa resgatada'), ('LEMBRETE_TAREFA', 'Lembrete de tarefa'), ('TAREFA_NAO_REALIZADA', 'Tarefa não realizada'), ('RESUMO_DIARIO', 'Resumo diário'), ('RESUMO_SEMANAL', 'Resumo semanal')], default='NIVEL_AVATAR', max_length=30),
        ),
        migrations.CreateModel(
            name='Recompensa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('descricao', models.TextField(blank=True)),
                ('icone', models.CharField(default='🎁', max_length=8)),
                ('custo_pontos', models.PositiveIntegerField(default=50)),
                ('categoria', models.CharField(choices=[('EXPERIENCIA', '❤️ Momento juntos'), ('PRIVILEGIO', '🎉 Privilégio'), ('TEMPO', '⏱️ Tempo especial'), ('OUTRO', '🎁 Outro')], default='EXPERIENCIA', max_length=20)),
                ('ativa', models.BooleanField(default=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('criada_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recompensas_criadas', to=settings.AUTH_USER_MODEL)),
                ('familia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recompensas', to='usuarios.familia')),
            ],
            options={
                'verbose_name': 'Recompensa',
                'verbose_name_plural': 'Recompensas',
                'ordering': ('custo_pontos', 'titulo'),
            },
        ),
        migrations.CreateModel(
            name='ResgateRecompensa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo_snapshot', models.CharField(max_length=120)),
                ('icone_snapshot', models.CharField(default='🎁', max_length=8)),
                ('custo_snapshot', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('SOLICITADO', 'Solicitado'), ('ENTREGUE', 'Entregue'), ('CANCELADO', 'Cancelado')], db_index=True, default='SOLICITADO', max_length=15)),
                ('solicitado_em', models.DateTimeField(auto_now_add=True)),
                ('concluido_em', models.DateTimeField(blank=True, null=True)),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resgates_recompensas', to='usuarios.perfilcrianca')),
                ('movimento_pontos', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resgate_recompensa', to='gamificacao.movimentopontos')),
                ('recompensa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resgates', to='gamificacao.recompensa')),
            ],
            options={
                'verbose_name': 'Resgate de recompensa',
                'verbose_name_plural': 'Resgates de recompensas',
                'ordering': ('-solicitado_em',),
            },
        ),
        migrations.CreateModel(
            name='ConquistaCrianca',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desbloqueada_em', models.DateTimeField(auto_now_add=True)),
                ('conquista', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='criancas', to='gamificacao.conquista')),
                ('crianca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conquistas_desbloqueadas', to='usuarios.perfilcrianca')),
            ],
            options={
                'verbose_name': 'Conquista da criança',
                'verbose_name_plural': 'Conquistas das crianças',
                'ordering': ('-desbloqueada_em',),
                'constraints': [models.UniqueConstraint(fields=('crianca', 'conquista'), name='conquista_crianca_unica')],
            },
        ),
    ]
