from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.models import PerfilCrianca, Usuario
from usuarios.views import obter_celebracao_usuario, obter_familia_tutor

from .forms import RecompensaForm
from .models import (
    Conquista,
    ConquistaCrianca,
    NotificacaoSistema,
    Recompensa,
    ResgateRecompensa,
)
from .services import (
    calcular_sequencia,
    cancelar_resgate,
    garantir_recompensas_padrao,
    melhor_sequencia,
    montar_painel_habilidades,
    resgatar_recompensa,
)


def _render_habilidades(
    request,
    perfil,
):
    painel = montar_painel_habilidades(
        perfil
    )

    radar = [
        {
            "nome": item["skill"].nome,
            "icone": item["skill"].icone,
            "valor": item["valor_radar"],
        }
        for item in painel
    ]

    return render(
        request,
        "gamificacao/habilidades/painel.html",
        {
            "perfil": perfil,
            "habilidades": painel,
            "radar": radar,
        },
    )


@login_required(login_url="login")
def minhas_habilidades(
    request,
):
    if request.user.tipo != Usuario.Tipo.CRIANCA:
        return redirect("inicio")

    perfil = getattr(
        request.user,
        "perfil_crianca",
        None,
    )

    if perfil is None:
        messages.error(
            request,
            (
                "Seu usuário não possui "
                "perfil infantil vinculado."
            ),
        )
        return redirect("inicio")

    return _render_habilidades(
        request,
        perfil,
    )


@login_required(login_url="login")
def habilidades_crianca_tutor(
    request,
    perfil_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    return _render_habilidades(
        request,
        perfil,
    )


def _dados_conquistas(
    perfil,
):
    desbloqueadas = {
        item.conquista_id: item
        for item in (
            ConquistaCrianca.objects
            .filter(
                crianca=perfil
            )
            .select_related(
                "conquista"
            )
        )
    }

    itens = []

    for conquista in (
        Conquista.objects
        .filter(ativa=True)
        .order_by(
            "ordem",
            "nome",
        )
    ):
        registro = desbloqueadas.get(
            conquista.id
        )

        itens.append(
            {
                "conquista": conquista,
                "desbloqueada": (
                    registro is not None
                ),
                "desbloqueada_em": (
                    registro.desbloqueada_em
                    if registro
                    else None
                ),
            }
        )

    desbloqueadas_lista = [
        item
        for item in itens
        if item["desbloqueada"]
    ]

    return {
        "itens": itens,
        "sequencia_atual": (
            calcular_sequencia(
                perfil
            )
        ),
        "melhor_sequencia": (
            melhor_sequencia(
                perfil
            )
        ),
        "total_desbloqueadas": len(
            desbloqueadas
        ),
        "conquista_destaque": (
            desbloqueadas_lista[0]
            if desbloqueadas_lista
            else None
        ),
    }


@login_required(login_url="login")
def minhas_conquistas(
    request,
):
    if request.user.tipo != Usuario.Tipo.CRIANCA:
        return redirect("inicio")

    perfil = getattr(
        request.user,
        "perfil_crianca",
        None,
    )

    if perfil is None:
        messages.error(
            request,
            "Perfil infantil não encontrado.",
        )
        return redirect("inicio")

    dados = _dados_conquistas(
        perfil
    )

    return render(
        request,
        "gamificacao/conquistas/painel.html",
        {
            "perfil": perfil,
            "celebracao_evento": (
                obter_celebracao_usuario(
                    request.user,
                    tipos=[
                        NotificacaoSistema
                        .Tipo
                        .CONQUISTA
                    ],
                )
            ),
            **dados,
        },
    )


@login_required(login_url="login")
def conquistas_crianca_tutor(
    request,
    perfil_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    dados = _dados_conquistas(
        perfil
    )

    return render(
        request,
        "gamificacao/conquistas/painel.html",
        {
            "perfil": perfil,
            **dados,
        },
    )


@login_required(login_url="login")
def loja_recompensas(
    request,
):
    if request.user.tipo == Usuario.Tipo.CRIANCA:
        perfil = getattr(
            request.user,
            "perfil_crianca",
            None,
        )

        if perfil is None:
            messages.error(
                request,
                "Perfil infantil não encontrado.",
            )
            return redirect("inicio")

        familia = perfil.familia
        criador = (
            familia.tutores.first()
        )

        if criador:
            garantir_recompensas_padrao(
                familia,
                criador,
            )

        recompensas = (
            Recompensa.objects
            .filter(
                familia=familia,
                ativa=True,
            )
            .order_by(
                "custo_pontos",
                "titulo",
            )
        )

        resgates = (
            ResgateRecompensa.objects
            .filter(
                crianca=perfil
            )
            .order_by(
                "-solicitado_em"
            )[:8]
        )

        return render(
            request,
            "gamificacao/recompensas/loja.html",
            {
                "perfil": perfil,
                "recompensas": recompensas,
                "resgates": resgates,
                "modo_tutor": False,
            },
        )

    familia = obter_familia_tutor(
        request.user
    )

    garantir_recompensas_padrao(
        familia,
        request.user,
    )

    recompensas = (
        Recompensa.objects
        .filter(
            familia=familia
        )
        .order_by(
            "ativa",
            "custo_pontos",
            "titulo",
        )
    )

    pendentes = (
        ResgateRecompensa.objects
        .filter(
            crianca__familia=familia,
            status=(
                ResgateRecompensa
                .Status
                .SOLICITADO
            ),
        )
        .select_related(
            "crianca",
            "recompensa",
        )
        .order_by(
            "solicitado_em"
        )
    )

    destaque_pendente = pendentes.first()

    return render(
        request,
        "gamificacao/recompensas/loja.html",
        {
            "recompensas": recompensas,
            "pendentes": pendentes,
            "destaque_pendente": destaque_pendente,
            "modo_tutor": True,
            "celebracao_evento": (
                obter_celebracao_usuario(
                    request.user,
                    tipos=[
                        NotificacaoSistema
                        .Tipo
                        .RECOMPENSA
                    ],
                )
            ),
        },
    )


@login_required(login_url="login")
def recompensa_criar(
    request,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    if request.method == "POST":
        form = RecompensaForm(
            request.POST
        )

        if form.is_valid():
            recompensa = form.save(
                commit=False
            )

            recompensa.familia = familia
            recompensa.criada_por = request.user
            recompensa.save()

            messages.success(
                request,
                "Recompensa criada!",
            )

            return redirect(
                "loja_recompensas"
            )
    else:
        form = RecompensaForm()

    return render(
        request,
        "gamificacao/recompensas/form.html",
        {
            "form": form,
            "titulo": "Nova recompensa",
        },
    )


@login_required(login_url="login")
def recompensa_editar(
    request,
    recompensa_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    recompensa = get_object_or_404(
        Recompensa,
        id=recompensa_id,
        familia=familia,
    )

    if request.method == "POST":
        form = RecompensaForm(
            request.POST,
            instance=recompensa,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Recompensa atualizada!",
            )

            return redirect(
                "loja_recompensas"
            )
    else:
        form = RecompensaForm(
            instance=recompensa
        )

    return render(
        request,
        "gamificacao/recompensas/form.html",
        {
            "form": form,
            "titulo": "Editar recompensa",
        },
    )


@login_required(login_url="login")
@require_POST
def recompensa_alternar(
    request,
    recompensa_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    recompensa = get_object_or_404(
        Recompensa,
        id=recompensa_id,
        familia=familia,
    )

    recompensa.ativa = not recompensa.ativa
    recompensa.save(
        update_fields=[
            "ativa",
            "atualizada_em",
        ]
    )

    messages.success(
        request,
        (
            "Recompensa disponibilizada."
            if recompensa.ativa
            else "Recompensa ocultada da loja."
        ),
    )

    return redirect(
        "loja_recompensas"
    )


@login_required(login_url="login")
@require_POST
def recompensa_resgatar(
    request,
    recompensa_id,
):
    if request.user.tipo != Usuario.Tipo.CRIANCA:
        return redirect("inicio")

    perfil = getattr(
        request.user,
        "perfil_crianca",
        None,
    )

    if perfil is None:
        return redirect("inicio")

    recompensa = get_object_or_404(
        Recompensa,
        id=recompensa_id,
        familia=perfil.familia,
        ativa=True,
    )

    try:
        resgatar_recompensa(
            perfil=perfil,
            recompensa=recompensa,
        )
    except ValueError as erro:
        messages.error(
            request,
            str(erro),
        )
    else:
        messages.success(
            request,
            (
                f"{recompensa.icone} "
                f"{recompensa.titulo} resgatada! "
                "Agora é só aguardar o responsável."
            ),
        )

    return redirect(
        "loja_recompensas"
    )


@login_required(login_url="login")
def resgates_recompensas(
    request,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    resgates = (
        ResgateRecompensa.objects
        .filter(
            crianca__familia=familia
        )
        .select_related(
            "crianca",
            "recompensa",
        )
        .order_by(
            "-solicitado_em"
        )
    )

    return render(
        request,
        "gamificacao/recompensas/resgates.html",
        {
            "resgates": resgates,
            "resgate_destaque": (
                resgates.filter(
                    status=(
                        ResgateRecompensa
                        .Status
                        .SOLICITADO
                    )
                ).first()
            ),
            "celebracao_evento": (
                obter_celebracao_usuario(
                    request.user,
                    tipos=[
                        NotificacaoSistema
                        .Tipo
                        .RECOMPENSA
                    ],
                )
            ),
        },
    )


@login_required(login_url="login")
@require_POST
def resgate_entregar(
    request,
    resgate_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    resgate = get_object_or_404(
        ResgateRecompensa,
        id=resgate_id,
        crianca__familia=familia,
        status=(
            ResgateRecompensa
            .Status
            .SOLICITADO
        ),
    )

    resgate.status = (
        ResgateRecompensa
        .Status
        .ENTREGUE
    )

    resgate.concluido_em = timezone.now()

    resgate.save(
        update_fields=[
            "status",
            "concluido_em",
        ]
    )

    messages.success(
        request,
        "Recompensa marcada como entregue.",
    )

    return redirect(
        "resgates_recompensas"
    )


@login_required(login_url="login")
@require_POST
def resgate_cancelar(
    request,
    resgate_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    resgate = get_object_or_404(
        ResgateRecompensa,
        id=resgate_id,
        crianca__familia=familia,
        status=(
            ResgateRecompensa
            .Status
            .SOLICITADO
        ),
    )

    try:
        cancelar_resgate(
            resgate=resgate,
            tutor=request.user,
        )
    except ValueError as erro:
        messages.error(
            request,
            str(erro),
        )
    else:
        messages.warning(
            request,
            (
                "Resgate cancelado e os pontos "
                "foram devolvidos."
            ),
        )

    return redirect(
        "resgates_recompensas"
    )


@login_required(login_url="login")
def notificacoes_central(request):
    filtro = request.GET.get(
        "filtro",
        "todas",
    )

    notificacoes = (
        NotificacaoSistema.objects
        .filter(
            usuario_destino=request.user
        )
        .select_related(
            "crianca",
            "tarefa",
            "skill",
        )
    )

    if filtro == "nao_lidas":
        notificacoes = notificacoes.filter(
            visualizada=False
        )

    contexto = {
        "notificacoes": notificacoes[:100],
        "filtro": filtro,
        "total_nao_lidas": (
            NotificacaoSistema.objects
            .filter(
                usuario_destino=request.user,
                visualizada=False,
            )
            .count()
        ),
    }

    return render(
        request,
        "gamificacao/notificacoes/central.html",
        contexto,
    )


@login_required(login_url="login")
def notificacao_abrir(
    request,
    notificacao_id,
):
    notificacao = get_object_or_404(
        NotificacaoSistema,
        id=notificacao_id,
        usuario_destino=request.user,
    )

    if not notificacao.visualizada:
        notificacao.visualizada = True
        notificacao.save(
            update_fields=["visualizada"]
        )

    destino = (
        notificacao.url_destino
        or ""
    )

    if destino.startswith("/"):
        return redirect(destino)

    return redirect(
        "notificacoes_central"
    )


@login_required(login_url="login")
@require_POST
def notificacoes_marcar_todas(request):
    NotificacaoSistema.objects.filter(
        usuario_destino=request.user,
        visualizada=False,
    ).update(
        visualizada=True
    )

    return redirect(
        "notificacoes_central"
    )
