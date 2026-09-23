from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GamificacaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gamificacao"

    def ready(self):
        from .catalogo import carregar_catalogo_padrao

        post_migrate.connect(
            carregar_catalogo_padrao,
            sender=self,
            dispatch_uid=(
                "gamificacao.carregar_catalogo_padrao"
            ),
        )
