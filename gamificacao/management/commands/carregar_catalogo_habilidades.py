from django.core.management.base import BaseCommand

from gamificacao.catalogo import carregar_catalogo_padrao
from gamificacao.models import Habilidade
from tarefas.models import SugestaoAtividade


class Command(BaseCommand):
    help = (
        "Cria ou atualiza Skills e tarefas predefinidas."
    )

    def handle(self, *args, **options):
        carregar_catalogo_padrao()

        total_skills = Habilidade.objects.filter(
            ativa=True
        ).count()

        total_sugestoes = SugestaoAtividade.objects.filter(
            ativa=True
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo atualizado: "
                f"{total_sugestoes} tarefas predefinidas e "
                f"{total_skills} Skills."
            )
        )
