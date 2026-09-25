

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tarefas', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instanciatarefa',
            name='status',
            field=models.CharField(choices=[('PENDENTE', 'Pendente'), ('REVISAO', 'Aguardando revisão'), ('APROVADA', 'Aprovada'), ('REJEITADA', 'Rejeitada'), ('NAO_REALIZADA', 'Não realizada')], db_index=True, default='PENDENTE', max_length=20),
        ),
    ]
