from django import template

from gamificacao.services import calcular_sequencia
from tarefas.services import calcular_indicadores_periodo


register = template.Library()


@register.simple_tag
def indicadores_semana_crianca(perfil):
    if not perfil:
        return {
            "taxa_conclusao": 0,
            "aprovadas": 0,
            "nao_realizadas": 0,
            "atrasadas": 0,
            "revisao": 0,
        }

    return calcular_indicadores_periodo(
        perfil=perfil,
        dias=7,
    )


@register.simple_tag
def sequencia_crianca(perfil):
    if not perfil:
        return 0

    return calcular_sequencia(perfil)
