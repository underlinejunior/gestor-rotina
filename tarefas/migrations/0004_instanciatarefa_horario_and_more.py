

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tarefas', '0003_sugestaotarefa'),
    ]

    operations = [
        migrations.AddField(
            model_name='instanciatarefa',
            name='horario',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='instanciatarefa',
            name='lembrete_ativo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='instanciatarefa',
            name='periodo',
            field=models.CharField(choices=[('QUALQUER', 'Qualquer horário'), ('MANHA', '🌅 Manhã'), ('TARDE', '☀️ Tarde'), ('NOITE', '🌙 Noite'), ('HORARIO', '🕐 Horário específico')], default='QUALQUER', max_length=12),
        ),
        migrations.AddField(
            model_name='moldetarefa',
            name='horario',
            field=models.TimeField(blank=True, null=True, verbose_name='Horário específico'),
        ),
        migrations.AddField(
            model_name='moldetarefa',
            name='lembrete_ativo',
            field=models.BooleanField(default=False, verbose_name='Lembrar desta tarefa'),
        ),
        migrations.AddField(
            model_name='moldetarefa',
            name='periodo',
            field=models.CharField(choices=[('QUALQUER', 'Qualquer horário'), ('MANHA', '🌅 Manhã'), ('TARDE', '☀️ Tarde'), ('NOITE', '🌙 Noite'), ('HORARIO', '🕐 Horário específico')], default='QUALQUER', max_length=12, verbose_name='Momento do dia'),
        ),
    ]
