from django.contrib import admin

from .models import (
    Conquista,
    ConquistaCrianca,
    InstanciaTarefaSkill,
    MoldeTarefaSkill,
    MovimentoPontos,
    MovimentoSkill,
    NotificacaoSistema,
    ProgressoSkill,
    Recompensa,
    ResgateRecompensa,
    Skill,
    SugestaoTarefaSkill,
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "icone",
        "nome",
        "slug",
        "ordem",
        "ativa",
    )
    list_filter = ("ativa",)
    search_fields = ("nome", "slug")


@admin.register(MoldeTarefaSkill)
class MoldeTarefaSkillAdmin(admin.ModelAdmin):
    list_display = (
        "molde",
        "skill",
        "impacto",
    )


@admin.register(InstanciaTarefaSkill)
class InstanciaTarefaSkillAdmin(admin.ModelAdmin):
    list_display = (
        "tarefa",
        "skill",
        "impacto",
        "xp_planejado",
    )


@admin.register(SugestaoTarefaSkill)
class SugestaoTarefaSkillAdmin(admin.ModelAdmin):
    list_display = (
        "sugestao",
        "skill",
        "impacto",
    )


@admin.register(ProgressoSkill)
class ProgressoSkillAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "skill",
        "xp_total",
        "nivel_atual",
        "atualizado_em",
    )
    list_filter = ("skill",)
    search_fields = (
        "crianca__nome",
        "skill__nome",
    )


@admin.register(MovimentoSkill)
class MovimentoSkillAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "skill",
        "xp",
        "nivel_antes",
        "nivel_depois",
        "criado_em",
    )
    list_filter = (
        "skill",
        "nivel_depois",
    )
    search_fields = (
        "crianca__nome",
        "tarefa__titulo",
    )


@admin.register(MovimentoPontos)
class MovimentoPontosAdmin(admin.ModelAdmin):
    list_display = (
        "crianca",
        "tipo",
        "pontos",
        "saldo_apos",
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
        "skill__nome",
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


@admin.register(ResgateRecompensa)
class ResgateRecompensaAdmin(admin.ModelAdmin):
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


@admin.register(ConquistaCrianca)
class ConquistaCriancaAdmin(admin.ModelAdmin):
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
