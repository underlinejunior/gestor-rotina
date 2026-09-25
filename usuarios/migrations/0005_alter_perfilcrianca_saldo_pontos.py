

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_usuario_boas_vindas_exibidas_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfilcrianca',
            name='saldo_pontos',
            field=models.IntegerField(default=0),
        ),
    ]
