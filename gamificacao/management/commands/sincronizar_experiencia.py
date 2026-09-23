from django.core.management.base import BaseCommand

from usuarios.models import PerfilCrianca


class Command(BaseCommand):
    help = (
        "Preserva o saldo positivo atual como XP histórico "
        "para perfis criados antes da separação saldo/XP."
    )

    def handle(self, *args, **options):
        atualizados = 0

        for perfil in PerfilCrianca.objects.all():
            base = max(
                int(perfil.pontos_experiencia or 0),
                int(perfil.saldo_pontos or 0),
                0,
            )

            if base != perfil.pontos_experiencia:
                perfil.pontos_experiencia = base
                perfil.save(
                    update_fields=[
                        "pontos_experiencia"
                    ]
                )
                atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{atualizados} perfil(is) sincronizado(s)."
            )
        )
