from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from tarefas.models import InstanciaTarefa


class Command(BaseCommand):
    help = (
        "Remove fotografias de evidência antigas de tarefas finalizadas, "
        "preservando o histórico textual e os indicadores."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=getattr(
                settings,
                "EVIDENCE_RETENTION_DAYS",
                180,
            ),
            help="Quantidade de dias de retenção das fotografias.",
        )

    def handle(self, *args, **options):
        dias = max(1, int(options["dias"]))
        limite = timezone.now() - timedelta(days=dias)

        tarefas = (
            InstanciaTarefa.objects
            .filter(
                enviada_em__lt=limite,
                status__in=[
                    InstanciaTarefa.Status.APROVADA,
                    InstanciaTarefa.Status.REJEITADA,
                    InstanciaTarefa.Status.NAO_REALIZADA,
                ],
            )
            .exclude(foto="")
            .exclude(foto__isnull=True)
        )

        removidas = 0

        for tarefa in tarefas.iterator():
            if not tarefa.foto:
                continue

            tarefa.foto.delete(save=False)
            tarefa.foto = None
            tarefa.save(
                update_fields=[
                    "foto",
                    "atualizada_em",
                ]
            )
            removidas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{removidas} evidência(s) removida(s) "
                f"com retenção superior a {dias} dia(s)."
            )
        )
