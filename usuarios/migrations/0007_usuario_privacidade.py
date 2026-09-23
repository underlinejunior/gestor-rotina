from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0006_perfilcrianca_pontos_experiencia_convitetutor"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="privacidade_aceita_em",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Política de privacidade aceita em",
            ),
        ),
        migrations.AddField(
            model_name="usuario",
            name="privacidade_versao",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                verbose_name="Versão da política de privacidade",
            ),
        ),
    ]
