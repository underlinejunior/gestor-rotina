from django.core.management.base import BaseCommand
from django.utils import timezone

from tarefas.services import (
    processar_lembretes,
)


class Command(BaseCommand):
    help = (
        "Cria notificações internas para tarefas "
        "que chegaram ao horário do lembrete."
    )

    def handle(self, *args, **options):
        quantidade = processar_lembretes(
            agora=timezone.localtime()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{quantidade} lembrete(s) criado(s)."
            )
        )
