from django.core.management.base import BaseCommand

from gamificacao.services import (
    avaliar_conquistas,
)
from usuarios.models import PerfilCrianca


class Command(BaseCommand):
    help = (
        "Recalcula conquistas com base no histórico "
        "já existente de cada criança."
    )

    def handle(self, *args, **options):
        total = 0

        for perfil in PerfilCrianca.objects.all():
            antes = (
                perfil
                .conquistas_desbloqueadas
                .count()
            )

            avaliar_conquistas(
                perfil
            )

            depois = (
                perfil
                .conquistas_desbloqueadas
                .count()
            )

            total += max(
                0,
                depois - antes,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{total} conquista(s) nova(s) desbloqueada(s)."
            )
        )
