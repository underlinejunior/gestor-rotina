

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_alter_perfilcrianca_saldo_pontos'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilcrianca',
            name='pontos_experiencia',
            field=models.PositiveIntegerField(default=0, verbose_name='XP histórico do avatar'),
        ),
        migrations.CreateModel(
            name='ConviteTutor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(db_index=True, max_length=12, unique=True)),
                ('expira_em', models.DateTimeField()),
                ('ativo', models.BooleanField(db_index=True, default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('utilizado_em', models.DateTimeField(blank=True, null=True)),
                ('criado_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='convites_tutor_criados', to=settings.AUTH_USER_MODEL)),
                ('familia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='convites_tutor', to='usuarios.familia')),
                ('usado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='convites_tutor_usados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Convite de responsável',
                'verbose_name_plural': 'Convites de responsáveis',
                'ordering': ('-criado_em',),
            },
        ),
    ]
