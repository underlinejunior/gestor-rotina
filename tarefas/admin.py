from django.contrib import admin

from .models import (
    TarefaAgendada,
    RotinaPlanejada,
    SugestaoAtividade,
)


@admin.register(RotinaPlanejada)
class RotinaPlanejadaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "crianca",
        "frequencia",
        "periodo",
        "horario",
        "lembrete_ativo",
        "pontos_base",
        "ativa",
    )

    list_filter = (
        "frequencia",
        "periodo",
        "lembrete_ativo",
        "ativa",
        "familia",
    )

    search_fields = (
        "titulo",
        "crianca__nome",
    )


@admin.register(TarefaAgendada)
class TarefaAgendadaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "crianca",
        "data_referencia",
        "status",
        "pontos_base",
        "pontos_concedidos",
    )

    list_filter = (
        "status",
        "origem",
        "data_referencia",
        "familia",
    )

    search_fields = (
        "titulo",
        "crianca__nome",
    )

    readonly_fields = (
        "criada_em",
        "atualizada_em",
    )


@admin.register(SugestaoAtividade)
class SugestaoAtividadeAdmin(admin.ModelAdmin):
    list_display = (
        "icone",
        "titulo",
        "categoria",
        "idade_minima",
        "idade_maxima",
        "pontos_sugeridos",
        "ativa",
    )

    list_filter = (
        "categoria",
        "ativa",
    )

    search_fields = (
        "titulo",
        "descricao",
    )
