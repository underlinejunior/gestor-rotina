from django.core.management.base import BaseCommand
from django.utils import timezone

from tarefas.services import processar_rotinas


class Command(BaseCommand):
    help = (
        "Encerra tarefas antigas pendentes "
        "e gera as tarefas do dia."
    )

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        resultado = processar_rotinas(
            data=hoje
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{resultado['criadas']} tarefa(s) "
                    "criada(s) e "
                    f"{resultado['encerradas']} tarefa(s) "
                    "antiga(s) marcada(s) como não realizada(s) "
                    f"em {hoje:%d/%m/%Y}."
                )
            )
        )
