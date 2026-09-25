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


@register.simple_tag
def indicadores_semana_crianca(perfil):
    """
    Retorna os indicadores dos últimos 7 dias para o card da criança.

    A importação é feita dentro da função para evitar acoplamento
    desnecessário durante o carregamento da biblioteca de template tags.
    """
    if not perfil:
        return {
            "taxa_conclusao": 0,
            "aprovadas": 0,
            "nao_realizadas": 0,
            "atrasadas": 0,
            "revisao": 0,
        }

    from tarefas.services import calcular_indicadores_periodo

    return calcular_indicadores_periodo(
        perfil=perfil,
        dias=7,
    )


@register.simple_tag
def sequencia_crianca(perfil):
    """
    Retorna a sequência atual da criança para o card unificado.
    """
    if not perfil:
        return 0

    from gamificacao.services import calcular_sequencia

    return calcular_sequencia(perfil)
