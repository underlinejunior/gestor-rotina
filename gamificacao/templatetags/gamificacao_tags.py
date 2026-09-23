from django import template

from gamificacao.models import NotificacaoSistema


register = template.Library()


@register.inclusion_tag(
    "gamificacao/notificacoes/painel_sino.html",
    takes_context=True,
)
def painel_notificacoes(
    context,
    usuario,
):
    if not usuario.is_authenticated:
        return {
            "usuario": usuario,
            "total_nao_lidas": 0,
            "notificacoes_recentes": [],
        }

    notificacoes = (
        NotificacaoSistema.objects
        .filter(
            usuario_destino=usuario
        )
        .select_related(
            "crianca",
            "tarefa",
            "skill",
        )
    )

    total_nao_lidas = notificacoes.filter(
        visualizada=False
    ).count()

    return {
        "usuario": usuario,
        "total_nao_lidas": total_nao_lidas,
        "notificacoes_recentes": (
            notificacoes
            .filter(
                visualizada=False
            )[:5]
        ),
        "request": context.get("request"),
    }
