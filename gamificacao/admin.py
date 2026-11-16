from django.contrib import admin

from .models import (
    Conquista,
    ConquistaInfantil,
    TarefaHabilidade,
    RotinaHabilidade,
    MovimentacaoPontos,
    MovimentacaoHabilidade,
    NotificacaoSistema,
    ProgressoHabilidade,
    Recompensa,
    SolicitacaoResgate,
    Habilidade,
    SugestaoHabilidade,
)


@admin.register(Habilidade)
class HabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "icone",
        "nome",
        "slug",
        "ordem",
        "ativa",
    )
    list_filter = ("ativa",)
    search_fields = ("nome", "slug")


@admin.register(RotinaHabilidade)
class RotinaHabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "rotina",
        "habilidade",
        "intensidade",
    )


@admin.register(TarefaHabilidade)
class TarefaHabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "tarefa",
        "habilidade",
        "intensidade",
        "experiencia_prevista",
    )


@admin.register(SugestaoHabilidade)
class SugestaoHabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "sugestao",
        "habilidade",
        "intensidade",
    )


@admin.register(ProgressoHabilidade)
class ProgressoHabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "habilidade",
        "experiencia_acumulada",
        "nivel_atual",
        "atualizado_em",
    )
    list_filter = ("habilidade",)
    search_fields = (
        "crianca__nome",
        "habilidade__nome",
    )


@admin.register(MovimentacaoHabilidade)
class MovimentacaoHabilidadeAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "habilidade",
        "xp",
        "nivel_antes",
        "nivel_depois",
        "criado_em",
    )
    list_filter = (
        "habilidade",
        "nivel_depois",
    )
    search_fields = (
        "crianca__nome",
        "tarefa__titulo",
    )


@admin.register(MovimentacaoPontos)
class MovimentacaoPontosAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "tipo",
        "pontos",
        "saldo_resultante",
        "nivel_antes",
        "nivel_depois",
        "criado_em",
    )
    list_filter = (
        "tipo",
        "nivel_depois",
        "criado_em",
    )
    search_fields = (
        "crianca__nome",
        "tarefa__titulo",
    )
    readonly_fields = (
        "criado_em",
    )


@admin.register(NotificacaoSistema)
class NotificacaoSistemaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "usuario_destino",
        "tipo",
        "crianca",
        "visualizada",
        "criada_em",
    )
    list_filter = (
        "tipo",
        "visualizada",
        "criada_em",
    )
    search_fields = (
        "titulo",
        "usuario_destino__username",
        "crianca__nome",
        "tarefa__titulo",
        "habilidade__nome",
        "chave",
    )
    readonly_fields = (
        "criada_em",
    )


@admin.register(Recompensa)
class RecompensaAdmin(admin.ModelAdmin):
    list_display = (
        "icone",
        "titulo",
        "familia",
        "custo_pontos",
        "categoria",
        "ativa",
    )

    list_filter = (
        "categoria",
        "ativa",
        "familia",
    )

    search_fields = (
        "titulo",
        "familia__nome",
    )


@admin.register(SolicitacaoResgate)
class SolicitacaoResgateAdmin(admin.ModelAdmin):
    list_display = (
        "titulo_snapshot",
        "crianca",
        "custo_snapshot",
        "status",
        "solicitado_em",
    )

    list_filter = (
        "status",
        "solicitado_em",
    )

    search_fields = (
        "titulo_snapshot",
        "crianca__nome",
    )


@admin.register(Conquista)
class ConquistaAdmin(admin.ModelAdmin):
    list_display = (
        "icone",
        "nome",
        "slug",
        "ordem",
        "ativa",
    )

    list_filter = ("ativa",)
    search_fields = ("nome", "slug")


@admin.register(ConquistaInfantil)
class ConquistaInfantilAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "conquista",
        "desbloqueada_em",
    )

    list_filter = (
        "conquista",
        "desbloqueada_em",
    )

    search_fields = (
        "crianca__nome",
        "conquista__nome",
    )
