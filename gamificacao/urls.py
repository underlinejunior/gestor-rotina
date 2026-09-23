from django.urls import path

from . import views


urlpatterns = [
    path(
        "minhas-habilidades/",
        views.minhas_habilidades,
        name="minhas_habilidades",
    ),
    path(
        "criancas/<int:perfil_id>/habilidades/",
        views.habilidades_crianca_tutor,
        name="habilidades_crianca_tutor",
    ),

    path(
        "minhas-conquistas/",
        views.minhas_conquistas,
        name="minhas_conquistas",
    ),
    path(
        "criancas/<int:perfil_id>/conquistas/",
        views.conquistas_crianca_tutor,
        name="conquistas_crianca_tutor",
    ),

    path(
        "recompensas/",
        views.loja_recompensas,
        name="loja_recompensas",
    ),
    path(
        "recompensas/nova/",
        views.recompensa_criar,
        name="recompensa_criar",
    ),
    path(
        "recompensas/<int:recompensa_id>/editar/",
        views.recompensa_editar,
        name="recompensa_editar",
    ),
    path(
        "recompensas/<int:recompensa_id>/alternar/",
        views.recompensa_alternar,
        name="recompensa_alternar",
    ),
    path(
        "recompensas/<int:recompensa_id>/resgatar/",
        views.recompensa_resgatar,
        name="recompensa_resgatar",
    ),
    path(
        "recompensas/resgates/",
        views.resgates_recompensas,
        name="resgates_recompensas",
    ),
    path(
        "recompensas/resgates/<int:resgate_id>/entregar/",
        views.resgate_entregar,
        name="resgate_entregar",
    ),
    path(
        "recompensas/resgates/<int:resgate_id>/cancelar/",
        views.resgate_cancelar,
        name="resgate_cancelar",
    ),

    path(
        "notificacoes/",
        views.notificacoes_central,
        name="notificacoes_central",
    ),
    path(
        "notificacoes/<int:notificacao_id>/abrir/",
        views.notificacao_abrir,
        name="notificacao_abrir",
    ),
    path(
        "notificacoes/marcar-todas/",
        views.notificacoes_marcar_todas,
        name="notificacoes_marcar_todas",
    ),
]
