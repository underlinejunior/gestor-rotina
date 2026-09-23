from django.urls import path

from . import views


urlpatterns = [
    path(
        "service-worker.js",
        views.service_worker_view,
        name="service_worker",
    ),
    path(
        "offline/",
        views.offline_view,
        name="offline",
    ),

    path(
        "privacidade/",
        views.privacidade_politica,
        name="privacidade_politica",
    ),
    path(
        "privacidade/aceite/",
        views.privacidade_aceite,
        name="privacidade_aceite",
    ),
    path(
        "privacidade/central/",
        views.privacidade_central,
        name="privacidade_central",
    ),
    path(
        "privacidade/exportar/",
        views.privacidade_exportar,
        name="privacidade_exportar",
    ),
    path(
        "privacidade/evidencias/apagar/",
        views.privacidade_apagar_evidencias,
        name="privacidade_apagar_evidencias",
    ),
    path(
        "privacidade/conta/excluir/",
        views.privacidade_excluir_conta,
        name="privacidade_excluir_conta",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "cadastro/",
        views.cadastro_tutor_view,
        name="cadastro_tutor",
    ),
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "",
        views.inicio_view,
        name="inicio",
    ),


    path(
        "familia/",
        views.familia_configuracao,
        name="familia_configuracao",
    ),
    path(
        "familia/convite/novo/",
        views.convite_tutor_criar,
        name="convite_tutor_criar",
    ),
    path(
        "familia/entrar/",
        views.familia_entrar_codigo,
        name="familia_entrar_codigo",
    ),
    path(
        "familia/convite/<int:convite_id>/cancelar/",
        views.convite_tutor_cancelar,
        name="convite_tutor_cancelar",
    ),

    path(
        "criancas/",
        views.criancas_listar,
        name="criancas_listar",
    ),
    path(
        "criancas/nova/",
        views.crianca_criar,
        name="crianca_criar",
    ),
    path(
        "criancas/<int:perfil_id>/editar/",
        views.crianca_editar,
        name="crianca_editar",
    ),
]
