

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamificacao', '0001_initial'),
        ('usuarios', '0004_usuario_boas_vindas_exibidas_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificacaoSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('NIVEL_AVATAR', 'Mudança de nível do avatar')], default='NIVEL_AVATAR', max_length=30)),
                ('titulo', models.CharField(max_length=150)),
                ('mensagem', models.TextField(blank=True)),
                ('nivel_anterior', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('nivel_novo', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('visualizada', models.BooleanField(default=False)),
                ('criada_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('crianca', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes_sistema', to='usuarios.perfilcrianca')),
                ('usuario_destino', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes_sistema', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notificação do sistema',
                'verbose_name_plural': 'Notificações do sistema',
                'ordering': ('-criada_em',),
            },
        ),
    ]
