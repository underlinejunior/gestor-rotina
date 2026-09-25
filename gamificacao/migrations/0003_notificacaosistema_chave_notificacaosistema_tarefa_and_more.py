

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamificacao', '0002_notificacaosistema'),
        ('tarefas', '0002_alter_instanciatarefa_status'),
        ('usuarios', '0004_usuario_boas_vindas_exibidas_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacaosistema',
            name='chave',
            field=models.CharField(blank=True, db_index=True, default='', help_text='Chave interna usada para evitar notificações duplicadas.', max_length=180),
        ),
        migrations.AddField(
            model_name='notificacaosistema',
            name='tarefa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notificacoes_sistema', to='tarefas.instanciatarefa'),
        ),
        migrations.AddField(
            model_name='notificacaosistema',
            name='url_destino',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='tipo',
            field=models.CharField(choices=[('NIVEL_AVATAR', 'Mudança de nível do avatar'), ('TAREFA_NAO_REALIZADA', 'Tarefa não realizada'), ('RESUMO_DIARIO', 'Resumo diário'), ('RESUMO_SEMANAL', 'Resumo semanal')], default='NIVEL_AVATAR', max_length=30),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='titulo',
            field=models.CharField(max_length=180),
        ),
        migrations.AlterField(
            model_name='notificacaosistema',
            name='visualizada',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddConstraint(
            model_name='notificacaosistema',
            constraint=models.UniqueConstraint(condition=models.Q(('chave', ''), _negated=True), fields=('usuario_destino', 'chave'), name='notif_chave_usuario_unica'),
        ),
    ]
