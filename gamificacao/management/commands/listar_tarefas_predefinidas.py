from django.core.management.base import BaseCommand

from gamificacao.catalogo import carregar_catalogo_padrao
from tarefas.models import SugestaoTarefa


class Command(BaseCommand):
    help = "Lista as tarefas predefinidas cadastradas."

    def handle(self, *args, **options):
        if not SugestaoTarefa.objects.filter(
            ativa=True
        ).exists():
            carregar_catalogo_padrao()

        sugestoes = (
            SugestaoTarefa.objects
            .filter(ativa=True)
            .order_by(
                "idade_minima",
                "ordem",
            )
        )

        self.stdout.write(
            f"Total: {sugestoes.count()} tarefa(s) predefinida(s)."
        )

        for item in sugestoes:
            self.stdout.write(
                (
                    f"{item.icone} {item.titulo} | "
                    f"{item.idade_minima}-{item.idade_maxima} anos | "
                    f"{item.pontos_sugeridos} pts"
                )
            )
