from uuid import UUID
from datetime import timedelta
import math

from django.db import transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilInfantil, Usuario

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
    dados_nivel_habilidade,
)


@transaction.atomic
def registrar_pontos_aprovacao(
    tarefa,
    tutor,
    pontos,
):
    if MovimentacaoPontos.objects.filter(
        tarefa=tarefa
    ).exists():
        raise ValueError(
            "Esta tarefa já possui movimentação de pontos."
        )

    perfil = (
        PerfilInfantil.objects
        .select_for_update()
        .get(pk=tarefa.crianca_id)
    )

    nivel_antes = perfil.avatar_nivel
    pontos = max(0, int(pontos))


    base_historica = max(
        int(perfil.pontos_experiencia or 0),
        int(perfil.saldo_pontos or 0),
        0,
    )

    perfil.saldo_pontos += pontos
    perfil.pontos_experiencia = (
        base_historica
        + pontos
    )

    perfil.save(
        update_fields=[
            "saldo_pontos",
            "pontos_experiencia",
        ]
    )

    nivel_depois = perfil.avatar_nivel

    movimento = MovimentacaoPontos.objects.create(
        crianca=perfil,
        tarefa=tarefa,
        tipo=MovimentacaoPontos.Tipo.APROVACAO,
        pontos=pontos,
        saldo_resultante=perfil.saldo_pontos,
        nivel_antes=nivel_antes,
        nivel_depois=nivel_depois,
        registrado_por=tutor,
    )

    if nivel_depois > nivel_antes:
        criar_notificacoes_evolucao(
            perfil=perfil,
            nivel_antes=nivel_antes,
            nivel_depois=nivel_depois,
            movimento=movimento,
        )

    return movimento


def criar_notificacoes_evolucao(
    *,
    perfil,
    nivel_antes,
    nivel_depois,
    movimento,
):
    usuarios_destino = list(
        perfil.familia.tutores.all()
    )

    if perfil.usuario_id:
        usuarios_destino.append(
            perfil.usuario
        )

    ids = set()

    for usuario in usuarios_destino:
        if not usuario or usuario.id in ids:
            continue

        ids.add(usuario.id)

        if usuario.tipo == Usuario.Tipo.CRIANCA:
            titulo = (
                f"🎉 Seu avatar chegou ao nível "
                f"{nivel_depois}!"
            )
            mensagem = (
                f"Você saiu do nível {nivel_antes} e agora está "
                f"no nível {nivel_depois}. Continue completando "
                "suas tarefas para evoluir ainda mais."
            )
            url_destino = reverse(
                "meu_historico"
            )
        else:
            titulo = (
                f"🎉 {perfil.nome_exibicao} subiu "
                f"para o nível {nivel_depois}!"
            )
            mensagem = (
                f"O avatar de {perfil.nome_exibicao} evoluiu do "
                f"nível {nivel_antes} para o nível {nivel_depois}."
            )
            url_destino = reverse(
                "historico_crianca_tutor",
                args=[perfil.id],
            )

        NotificacaoSistema.objects.get_or_create(
            usuario_destino=usuario,
            chave=f"nivel:{movimento.id}:{usuario.id}",
            defaults={
                "crianca": perfil,
                "tipo": NotificacaoSistema.Tipo.NIVEL_AVATAR,
                "titulo": titulo,
                "mensagem": mensagem,
                "nivel_anterior": nivel_antes,
                "nivel_novo": nivel_depois,
                "url_destino": url_destino,
            },
        )


def salvar_habilidades_rotina(
    rotina,
    intensidades,
):
    RotinaHabilidade.objects.filter(
        rotina=rotina
    ).delete()

    novos = []

    for habilidade_id, intensidade in intensidades.items():
        if intensidade not in {
            Habilidade.Intensidade.BAIXA,
            Habilidade.Intensidade.MEDIA,
            Habilidade.Intensidade.ALTA,
        }:
            continue

        novos.append(
            RotinaHabilidade(
                rotina=rotina,
                habilidade_id=habilidade_id,
                intensidade=intensidade,
            )
        )

    if novos:
        RotinaHabilidade.objects.bulk_create(
            novos
        )


def copiar_habilidades_rotina_para_tarefa(
    rotina,
    tarefa,
):
    if tarefa.habilidades_tarefa.exists():
        return

    associacoes = (
        RotinaHabilidade.objects
        .filter(rotina=rotina)
        .select_related("habilidade")
    )

    snapshots = []

    for associacao in associacoes:
        snapshots.append(
            TarefaHabilidade(
                tarefa=tarefa,
                habilidade=associacao.habilidade,
                nome_snapshot=associacao.habilidade.nome,
                icone_snapshot=associacao.habilidade.icone,
                intensidade=associacao.intensidade,
                experiencia_prevista=Habilidade.calcular_experiencia(
                    associacao.intensidade
                ),
            )
        )

    if snapshots:
        TarefaHabilidade.objects.bulk_create(
            snapshots
        )


def salvar_habilidades_tarefa_bonus(
    tarefa,
    intensidades,
):
    snapshots = []

    skills = {
        habilidade.id: habilidade
        for habilidade in Habilidade.objects.filter(
            id__in=intensidades.keys(),
            ativa=True,
        )
    }

    for habilidade_id, intensidade in intensidades.items():
        try:
            identificador = UUID(str(habilidade_id))
        except (TypeError, ValueError, AttributeError):
            continue
        habilidade = skills.get(identificador)

        if not habilidade:
            continue

        if intensidade not in {
            Habilidade.Intensidade.BAIXA,
            Habilidade.Intensidade.MEDIA,
            Habilidade.Intensidade.ALTA,
        }:
            continue

        snapshots.append(
            TarefaHabilidade(
                tarefa=tarefa,
                habilidade=habilidade,
                nome_snapshot=habilidade.nome,
                icone_snapshot=habilidade.icone,
                intensidade=intensidade,
                experiencia_prevista=Habilidade.calcular_experiencia(
                    intensidade
                ),
            )
        )

    if snapshots:
        TarefaHabilidade.objects.bulk_create(
            snapshots
        )


def calcular_sequencia_constancia(perfil, hoje=None):
    """Sequência atual da habilidade Constância, por rotina diária repetida.

    Conta apenas datas com tarefas APROVADAS, relacionadas à mesma
    RotinaPlanejada e com a habilidade `constancia` associada à tarefa.
    Uma ou mais tarefas aprovadas no mesmo dia contam como um único dia.
    A sequência pode terminar hoje ou ontem; um dia ainda em andamento
    não apaga a sequência. Um dia inteiro sem aprovação interrompe-a.
    A consulta deriva o contador das aprovações, sem duplicar estado no banco.
    """
    from tarefas.models import TarefaAgendada

    hoje = hoje or timezone.localdate()
    datas_por_rotina = {}
    linhas = (
        TarefaAgendada.objects.filter(
            crianca=perfil,
            status=TarefaAgendada.Status.APROVADA,
            rotina__isnull=False,
            rotina__frequencia="DIARIA",
            data_referencia__lte=hoje,
            habilidades_tarefa__habilidade__slug="constancia",
        )
        .values_list("rotina_id", "data_referencia")
        .distinct()
    )
    for rotina_id, dia in linhas:
        datas_por_rotina.setdefault(rotina_id, set()).add(dia)

    melhor_atual = 0
    for dias in datas_por_rotina.values():
        if hoje in dias:
            cursor = hoje
        elif (hoje - timedelta(days=1)) in dias:
            cursor = hoje - timedelta(days=1)
        else:
            continue
        contador = 0
        while cursor in dias:
            contador += 1
            cursor -= timedelta(days=1)
        melhor_atual = max(melhor_atual, contador)

    return melhor_atual


@transaction.atomic
def registrar_xp_habilidades_aprovacao(
    tarefa,
):
    snapshots = list(
        tarefa
        .habilidades_tarefa
        .select_related("habilidade")
        .all()
    )

    evolucoes = []

    for snapshot in snapshots:
        if MovimentacaoHabilidade.objects.filter(
            tarefa=tarefa,
            habilidade=snapshot.habilidade,
        ).exists():
            continue

        progresso, _ = (
            ProgressoHabilidade.objects
            .select_for_update()
            .get_or_create(
                crianca=tarefa.crianca,
                habilidade=snapshot.habilidade,
                defaults={"experiencia_acumulada": 0},
            )
        )

        # Constância é contada por dias consecutivos da mesma rotina,
        # e não por XP ou intensidade. O contador é calculado a partir
        # das tarefas aprovadas, evitando duplicações ou estado obsoleto.
        if snapshot.habilidade.slug == "constancia":
            MovimentacaoHabilidade.objects.create(
                crianca=tarefa.crianca,
                habilidade=snapshot.habilidade,
                tarefa=tarefa,
                xp=0,
                nivel_antes=progresso.nivel_atual,
                nivel_depois=progresso.nivel_atual,
            )
            continue

        nivel_antes = progresso.nivel_atual

        progresso.experiencia_acumulada += snapshot.experiencia_prevista
        progresso.save(
            update_fields=[
                "experiencia_acumulada",
                "atualizado_em",
            ]
        )

        nivel_depois = progresso.nivel_atual

        movimento = MovimentacaoHabilidade.objects.create(
            crianca=tarefa.crianca,
            habilidade=snapshot.habilidade,
            tarefa=tarefa,
            xp=snapshot.experiencia_prevista,
            nivel_antes=nivel_antes,
            nivel_depois=nivel_depois,
        )

        if nivel_depois > nivel_antes:
            evolucoes.append(
                {
                    "habilidade": snapshot.habilidade,
                    "movimento": movimento,
                    "nivel_antes": nivel_antes,
                    "nivel_depois": nivel_depois,
                    "titulo_novo": dados_nivel_habilidade(
                        progresso.experiencia_acumulada
                    )["titulo"],
                }
            )

            criar_notificacoes_evolucao_habilidade(
                perfil=tarefa.crianca,
                habilidade=snapshot.habilidade,
                movimento=movimento,
                nivel_antes=nivel_antes,
                nivel_depois=nivel_depois,
            )

    return evolucoes


def criar_notificacoes_evolucao_habilidade(
    *,
    perfil,
    habilidade,
    movimento,
    nivel_antes,
    nivel_depois,
):
    usuarios = list(
        perfil.familia.tutores.all()
    )

    if perfil.usuario_id:
        usuarios.append(
            perfil.usuario
        )

    ids = set()

    for usuario in usuarios:
        if not usuario or usuario.id in ids:
            continue

        ids.add(usuario.id)

        if usuario.tipo == Usuario.Tipo.CRIANCA:
            titulo = (
                f"{habilidade.icone} {habilidade.nome} evoluiu!"
            )
            mensagem = (
                f"Sua habilidade {habilidade.nome} avançou do nível "
                f"{nivel_antes} para o nível {nivel_depois}."
            )
            url_destino = reverse(
                "minhas_habilidades"
            )
        else:
            titulo = (
                f"{habilidade.icone} {habilidade.nome} de "
                f"{perfil.nome_exibicao} evoluiu"
            )
            mensagem = (
                f"A prática de atividades ligadas a {habilidade.nome} "
                f"avançou do nível {nivel_antes} para "
                f"o nível {nivel_depois}."
            )
            url_destino = reverse(
                "habilidades_crianca_tutor",
                args=[perfil.id],
            )

        NotificacaoSistema.objects.get_or_create(
            usuario_destino=usuario,
            chave=f"habilidade:{movimento.id}:{usuario.id}",
            defaults={
                "crianca": perfil,
                "habilidade": habilidade,
                "tipo": NotificacaoSistema.Tipo.NIVEL_HABILIDADE,
                "titulo": titulo,
                "mensagem": mensagem,
                "nivel_anterior": nivel_antes,
                "nivel_novo": nivel_depois,
                "url_destino": url_destino,
            },
        )


def montar_painel_habilidades(
    perfil,
):
    skills = list(
        Habilidade.objects
        .filter(ativa=True)
        .order_by("ordem", "nome")
    )

    progressos = {
        item.habilidade_id: item
        for item in (
            ProgressoHabilidade.objects
            .filter(
                crianca=perfil,
                habilidade__in=skills,
            )
            .select_related("habilidade")
        )
    }

    inicio_recente = (
        timezone.now()
        - timedelta(days=30)
    )

    recentes = {
        item["habilidade_id"]: (
            item["total"] or 0
        )
        for item in (
            MovimentacaoHabilidade.objects
            .filter(
                crianca=perfil,
                habilidade__in=skills,
                criado_em__gte=inicio_recente,
            )
            .values("habilidade_id")
            .annotate(total=Sum("xp"))
        )
    }

    painel = []

    for habilidade in skills:
        progresso = progressos.get(
            habilidade.id
        )

        experiencia_acumulada = (
            progresso.experiencia_acumulada
            if progresso
            else 0
        )

        dados = dados_nivel_habilidade(
            experiencia_acumulada
        )

        xp_recente = recentes.get(
            habilidade.id,
            0,
        )

        if xp_recente >= 40:
            pratica_recente = "Muito praticada"
        elif xp_recente >= 20:
            pratica_recente = "Praticada"
        elif xp_recente > 0:
            pratica_recente = "Em prática"
        else:
            pratica_recente = "Sem prática recente"

        valor_radar = (
            (dados["nivel"] - 1)
            + (
                dados["percentual"]
                / 100
            )
        )

        sequencia_constancia = (
            calcular_sequencia_constancia(perfil)
            if habilidade.slug == "constancia"
            else None
        )
        if sequencia_constancia is not None:
            # Escala visual de 1 a 5 para o radar; 7 dias representam
            # a faixa máxima. O valor mostrado no card segue em dias.
            valor_radar = 1 + (4 * min(sequencia_constancia, 7) / 7)
            pratica_recente = f"{sequencia_constancia} dias em sequência"

        painel.append(
            {
                "sequencia_constancia": sequencia_constancia,
                "eh_constancia": habilidade.slug == "constancia",
                "habilidade": habilidade,
                "experiencia_acumulada": experiencia_acumulada,
                "nivel": dados["nivel"],
                "titulo_nivel": dados["titulo"],
                "percentual": dados["percentual"],
                "faltam": dados["faltam"],
                "xp_30_dias": xp_recente,
                "pratica_recente": pratica_recente,
                "valor_radar": round(
                    min(5, valor_radar),
                    2,
                ),
            }
        )

    return painel


@transaction.atomic
def registrar_penalidade_tarefa_nao_realizada(
    tarefa,
):
    """
    Deduz 50% dos pontos-base quando a tarefa é encerrada
    como NÃO REALIZADA.

    Como o saldo é inteiro, metades fracionárias são
    arredondadas para cima:
        5 pontos -> penalidade de 3
        10 pontos -> penalidade de 5
    """

    movimento_existente = (
        MovimentacaoPontos.objects
        .filter(tarefa=tarefa)
        .first()
    )

    if movimento_existente:
        return movimento_existente

    perfil = (
        PerfilInfantil.objects
        .select_for_update()
        .get(pk=tarefa.crianca_id)
    )

    nivel_antes = perfil.avatar_nivel

    penalidade = max(
        1,
        math.ceil(
            tarefa.pontos_base
            / 2
        ),
    )


    perfil.pontos_experiencia = max(
        int(perfil.pontos_experiencia or 0),
        int(perfil.saldo_pontos or 0),
        0,
    )

    perfil.saldo_pontos -= penalidade

    perfil.save(
        update_fields=[
            "saldo_pontos",
            "pontos_experiencia",
        ]
    )

    nivel_depois = perfil.avatar_nivel

    return MovimentacaoPontos.objects.create(
        crianca=perfil,
        tarefa=tarefa,
        tipo=MovimentacaoPontos.Tipo.PENALIDADE,
        pontos=-penalidade,
        saldo_resultante=perfil.saldo_pontos,
        nivel_antes=nivel_antes,
        nivel_depois=nivel_depois,
        registrado_por=None,
    )

def criar_alertas_tarefa_nao_realizada(
    tarefa,
    movimento=None,
):
    perfil = tarefa.crianca

    if movimento is not None:
        penalidade = abs(
            movimento.pontos
        )
    else:
        penalidade = max(
            1,
            math.ceil(
                tarefa.pontos_base
                / 2
            ),
        )

    for tutor in tarefa.familia.tutores.all():
        NotificacaoSistema.objects.get_or_create(
            usuario_destino=tutor,
            chave=(
                f"nao-realizada:"
                f"{tarefa.id}:"
                f"{tutor.id}"
            ),
            defaults={
                "crianca": perfil,
                "tarefa": tarefa,
                "tipo": NotificacaoSistema.Tipo.TAREFA_NAO_REALIZADA,
                "titulo": (
                    f"{perfil.nome_exibicao} não realizou "
                    f'"{tarefa.titulo}"'
                ),
                "mensagem": (
                    "A tarefa terminou o prazo sem uma "
                    "conclusão aprovada. Foram deduzidos "
                    f"{penalidade} ponto(s) do saldo."
                ),
                "url_destino": reverse(
                    "historico_crianca_tutor",
                    args=[perfil.id],
                ),
            },
        )


def gerar_resumos_familia(
    *,
    familia,
    hoje,
):
    from tarefas.models import TarefaAgendada

    ontem = hoje - timedelta(days=1)

    tarefas_ontem = TarefaAgendada.objects.filter(
        familia=familia,
        data_referencia=ontem,
    )

    if tarefas_ontem.exists():
        aprovadas = tarefas_ontem.filter(
            status=TarefaAgendada.Status.APROVADA
        ).count()

        nao_realizadas = tarefas_ontem.filter(
            status=TarefaAgendada.Status.NAO_REALIZADA
        ).count()

        revisao = tarefas_ontem.filter(
            status=TarefaAgendada.Status.REVISAO
        ).count()

        finalizadas = aprovadas + nao_realizadas

        taxa = (
            round(
                aprovadas
                / finalizadas
                * 100
            )
            if finalizadas
            else 0
        )

        for tutor in familia.tutores.all():
            NotificacaoSistema.objects.get_or_create(
                usuario_destino=tutor,
                chave=(
                    f"resumo-diario:"
                    f"{familia.id}:"
                    f"{ontem.isoformat()}:"
                    f"{tutor.id}"
                ),
                defaults={
                    "tipo": NotificacaoSistema.Tipo.RESUMO_DIARIO,
                    "titulo": (
                        f"Resumo de ontem: "
                        f"{taxa}% de conclusão"
                    ),
                    "mensagem": (
                        f"{aprovadas} aprovada(s), "
                        f"{nao_realizadas} não realizada(s) "
                        f"e {revisao} aguardando revisão."
                    ),
                    "url_destino": reverse(
                        "notificacoes_central"
                    ),
                },
            )

    if hoje.weekday() != 0:
        return

    fim = hoje - timedelta(days=1)
    inicio = hoje - timedelta(days=7)

    tarefas_semana = TarefaAgendada.objects.filter(
        familia=familia,
        data_referencia__gte=inicio,
        data_referencia__lte=fim,
    )

    if not tarefas_semana.exists():
        return

    aprovadas = tarefas_semana.filter(
        status=TarefaAgendada.Status.APROVADA
    ).count()

    nao_realizadas = tarefas_semana.filter(
        status=TarefaAgendada.Status.NAO_REALIZADA
    ).count()

    finalizadas = aprovadas + nao_realizadas

    taxa = (
        round(
            aprovadas
            / finalizadas
            * 100
        )
        if finalizadas
        else 0
    )

    for tutor in familia.tutores.all():
        NotificacaoSistema.objects.get_or_create(
            usuario_destino=tutor,
            chave=(
                f"resumo-semanal:"
                f"{familia.id}:"
                f"{inicio.isoformat()}:"
                f"{tutor.id}"
            ),
            defaults={
                "tipo": NotificacaoSistema.Tipo.RESUMO_SEMANAL,
                "titulo": (
                    f"Resumo da semana: "
                    f"{taxa}% de conclusão"
                ),
                "mensagem": (
                    f"Entre {inicio:%d/%m} e {fim:%d/%m}: "
                    f"{aprovadas} aprovada(s) e "
                    f"{nao_realizadas} não realizada(s)."
                ),
                "url_destino": reverse(
                    "notificacoes_central"
                ),
            },
        )


RECOMPENSAS_PADRAO = [
    {
        "icone": "🤗",
        "titulo": "Abraço gigante",
        "descricao": "Um momento especial de carinho em família.",
        "custo_pontos": 20,
        "categoria": Recompensa.Categoria.EXPERIENCIA,
    },
    {
        "icone": "🎲",
        "titulo": "Escolher uma brincadeira",
        "descricao": "Escolher uma brincadeira para fazer em família.",
        "custo_pontos": 50,
        "categoria": Recompensa.Categoria.EXPERIENCIA,
    },
    {
        "icone": "🎬",
        "titulo": "Escolher o filme",
        "descricao": "Escolher o filme da próxima sessão em família.",
        "custo_pontos": 80,
        "categoria": Recompensa.Categoria.PRIVILEGIO,
    },
    {
        "icone": "🍳",
        "titulo": "Cozinhar juntos",
        "descricao": "Escolher uma receita simples para preparar em família.",
        "custo_pontos": 100,
        "categoria": Recompensa.Categoria.EXPERIENCIA,
    },
    {
        "icone": "🚲",
        "titulo": "Passeio especial",
        "descricao": "Combinar um passeio especial com a família.",
        "custo_pontos": 150,
        "categoria": Recompensa.Categoria.EXPERIENCIA,
    },
]


def garantir_recompensas_padrao(
    familia,
    usuario,
):
    if Recompensa.objects.filter(
        familia=familia
    ).exists():
        return

    for item in RECOMPENSAS_PADRAO:
        Recompensa.objects.create(
            familia=familia,
            criada_por=usuario,
            **item,
        )


@transaction.atomic
def resgatar_recompensa(
    *,
    perfil,
    recompensa,
    tutor_solicitante=None,
):
    perfil = (
        PerfilInfantil.objects
        .select_for_update()
        .get(pk=perfil.pk)
    )
    if tutor_solicitante is not None:
        from usuarios.models import Usuario, Familia
        if (not getattr(tutor_solicitante, "is_authenticated", False)
            or tutor_solicitante.tipo != Usuario.Tipo.TUTOR
            or not Familia.objects.filter(
                pk=perfil.familia_id, tutores=tutor_solicitante
            ).exists()):
            raise ValueError("Somente um tutor desta família pode registrar o resgate.")
        if perfil.acesso_proprio:
            raise ValueError("Use a conta da criança para resgates com acesso próprio.")


    if not recompensa.ativa:
        raise ValueError(
            "Esta recompensa não está disponível."
        )

    if recompensa.familia_id != perfil.familia_id:
        raise ValueError(
            "Esta recompensa não pertence à família."
        )

    if perfil.saldo_pontos < recompensa.custo_pontos:
        faltam = (
            recompensa.custo_pontos
            - perfil.saldo_pontos
        )

        raise ValueError(
            f"Faltam {faltam} ponto(s) para esta recompensa."
        )


    perfil.pontos_experiencia = max(
        int(perfil.pontos_experiencia or 0),
        int(perfil.saldo_pontos or 0),
        0,
    )

    perfil.saldo_pontos -= recompensa.custo_pontos

    perfil.save(
        update_fields=[
            "saldo_pontos",
            "pontos_experiencia",
        ]
    )

    movimento = MovimentacaoPontos.objects.create(
        crianca=perfil,
        tarefa=None,
        tipo=MovimentacaoPontos.Tipo.RESGATE,
        pontos=-recompensa.custo_pontos,
        saldo_resultante=perfil.saldo_pontos,
        nivel_antes=perfil.avatar_nivel,
        nivel_depois=perfil.avatar_nivel,
        registrado_por=tutor_solicitante,
    )

    resgate = SolicitacaoResgate.objects.create(
        crianca=perfil,
        recompensa=recompensa,
        titulo_snapshot=recompensa.titulo,
        icone_snapshot=recompensa.icone,
        custo_snapshot=recompensa.custo_pontos,
        movimentacao_pontos=movimento,
        registrado_por=tutor_solicitante,
        escolha_assistida=tutor_solicitante is not None,
    )
    movimento.resgate = resgate
    movimento.save(update_fields=["resgate"])

    for tutor in perfil.familia.tutores.all():
        NotificacaoSistema.objects.get_or_create(
            usuario_destino=tutor,
            chave=(
                f"resgate:"
                f"{resgate.id}:"
                f"{tutor.id}"
            ),
            defaults={
                "crianca": perfil,
                "tipo": (
                    NotificacaoSistema
                    .Tipo
                    .RECOMPENSA
                ),
                "titulo": (
                    f"{recompensa.icone} "
                    f"{perfil.nome_exibicao} resgatou "
                    f"{recompensa.titulo}"
                ),
                "mensagem": (
                    f"Foram usados "
                    f"{recompensa.custo_pontos} pontos. "
                    "Confirme a entrega na área de recompensas."
                ),
                "url_destino": reverse(
                    "resgates_recompensas"
                ),
            },
        )

    return resgate


@transaction.atomic
def confirmar_entrega_resgate(*, resgate, tutor):
    """Conclui o resgate com a mesma regra de autorização do cancelamento.

    A trava e a condição de status impedem decisões simultâneas contraditórias.
    """
    from usuarios.models import Familia, Usuario

    resgate = SolicitacaoResgate.objects.select_for_update().get(pk=resgate.pk)
    if (
        not getattr(tutor, "is_authenticated", False)
        or tutor.tipo != Usuario.Tipo.TUTOR
        or not Familia.objects.filter(
            pk=resgate.crianca.familia_id, tutores=tutor
        ).exists()
    ):
        raise ValueError("O tutor não pertence à família deste resgate.")
    if resgate.status != SolicitacaoResgate.Status.SOLICITADO:
        raise ValueError("Apenas resgates solicitados podem ser entregues.")

    resgate.status = SolicitacaoResgate.Status.ENTREGUE
    resgate.concluido_em = timezone.now()
    resgate.save(update_fields=["status", "concluido_em"])
    return resgate


@transaction.atomic
def cancelar_resgate(
    *,
    resgate,
    tutor,
):
    # Trava o pedido antes de verificar seu status; evita duas restituições
    # concorrentes ao mesmo resgate.
    resgate = (
        SolicitacaoResgate.objects
        .select_for_update()
        .get(pk=resgate.pk)
    )

    # Valida a autorização mesmo quando o serviço não é chamado por uma view.
    from usuarios.models import Familia, Usuario
    if (
        not getattr(tutor, "is_authenticated", False)
        or tutor.tipo != Usuario.Tipo.TUTOR
        or not Familia.objects.filter(
            pk=resgate.crianca.familia_id, tutores=tutor
        ).exists()
    ):
        raise ValueError("O tutor não pertence à família deste resgate.")

    if (
        resgate.status
        != SolicitacaoResgate
        .Status
        .SOLICITADO
    ):
        raise ValueError(
            "Apenas resgates pendentes podem ser cancelados."
        )

    perfil = (
        PerfilInfantil.objects
        .select_for_update()
        .get(pk=resgate.crianca_id)
    )

    perfil.saldo_pontos += resgate.custo_snapshot

    perfil.save(
        update_fields=[
            "saldo_pontos",
        ]
    )

    MovimentacaoPontos.objects.create(
        crianca=perfil,
        tarefa=None,
        resgate=resgate,
        tipo=MovimentacaoPontos.Tipo.AJUSTE,
        pontos=resgate.custo_snapshot,
        saldo_resultante=perfil.saldo_pontos,
        nivel_antes=perfil.avatar_nivel,
        nivel_depois=perfil.avatar_nivel,
        registrado_por=tutor,
    )

    resgate.status = (
        SolicitacaoResgate
        .Status
        .CANCELADO
    )

    resgate.concluido_em = timezone.now()

    resgate.save(
        update_fields=[
            "status",
            "concluido_em",
        ]
    )

    return resgate


def calcular_sequencia(
    perfil,
    limite_dias=90,
):
    """
    Conta dias de rotina cumpridos em sequência.

    Dias sem tarefas não quebram a sequência. O dia atual só
    quebra a sequência se já estiver totalmente encerrado; tarefas
    pendentes de hoje são ignoradas porque ainda podem ser feitas.
    """
    from tarefas.models import TarefaAgendada

    hoje = timezone.localdate()

    inicio = (
        hoje
        - timedelta(
            days=limite_dias
        )
    )

    tarefas = list(
        TarefaAgendada.objects
        .filter(
            crianca=perfil,
            data_referencia__gte=inicio,
            data_referencia__lte=hoje,
        )
        .values(
            "data_referencia",
            "status",
        )
        .order_by(
            "-data_referencia"
        )
    )

    por_data = {}

    for item in tarefas:
        por_data.setdefault(
            item["data_referencia"],
            [],
        ).append(
            item["status"]
        )

    sequencia = 0

    for data in sorted(
        por_data.keys(),
        reverse=True,
    ):
        status_dia = por_data[data]

        if (
            data == hoje
            and any(
                status in {
                    "PENDENTE",
                    "REVISAO",
                    "REJEITADA",
                }
                for status in status_dia
            )
        ):
            continue

        if (
            status_dia
            and all(
                status == "APROVADA"
                for status in status_dia
            )
        ):
            sequencia += 1
            continue

        break

    return sequencia


def melhor_sequencia(
    perfil,
    limite_dias=365,
):
    from tarefas.models import TarefaAgendada

    hoje = timezone.localdate()

    inicio = (
        hoje
        - timedelta(
            days=limite_dias
        )
    )

    tarefas = (
        TarefaAgendada.objects
        .filter(
            crianca=perfil,
            data_referencia__gte=inicio,
            data_referencia__lte=hoje,
        )
        .values(
            "data_referencia",
            "status",
        )
        .order_by(
            "data_referencia"
        )
    )

    por_data = {}

    for item in tarefas:
        por_data.setdefault(
            item["data_referencia"],
            [],
        ).append(
            item["status"]
        )

    atual = 0
    melhor = 0

    for data in sorted(
        por_data.keys()
    ):
        status_dia = por_data[data]

        if (
            status_dia
            and all(
                status == "APROVADA"
                for status in status_dia
            )
        ):
            atual += 1
            melhor = max(
                melhor,
                atual,
            )
        else:
            atual = 0

    return melhor


def _desbloquear_conquista(
    *,
    perfil,
    slug,
):
    conquista = (
        Conquista.objects
        .filter(
            slug=slug,
            ativa=True,
        )
        .first()
    )

    if not conquista:
        return None

    registro, criada = (
        ConquistaInfantil.objects
        .get_or_create(
            crianca=perfil,
            conquista=conquista,
        )
    )

    if not criada:
        return None

    destinos = list(
        perfil.familia.tutores.all()
    )

    if perfil.usuario_id:
        destinos.append(
            perfil.usuario
        )

    ids = set()

    for usuario in destinos:
        if (
            not usuario
            or usuario.id in ids
        ):
            continue

        ids.add(
            usuario.id
        )

        if (
            usuario.tipo
            == Usuario.Tipo.CRIANCA
        ):
            titulo = (
                f"{conquista.icone} "
                f"Nova conquista: "
                f"{conquista.nome}"
            )
            mensagem = conquista.descricao
            url_destino = reverse(
                "minhas_conquistas"
            )
        else:
            titulo = (
                f"{conquista.icone} "
                f"{perfil.nome_exibicao} desbloqueou "
                f"{conquista.nome}"
            )
            mensagem = conquista.descricao
            url_destino = reverse(
                "conquistas_crianca_tutor",
                args=[
                    perfil.id
                ],
            )

        NotificacaoSistema.objects.get_or_create(
            usuario_destino=usuario,
            chave=(
                f"conquista:"
                f"{registro.id}:"
                f"{usuario.id}"
            ),
            defaults={
                "crianca": perfil,
                "tipo": (
                    NotificacaoSistema
                    .Tipo
                    .CONQUISTA
                ),
                "titulo": titulo,
                "mensagem": mensagem,
                "url_destino": url_destino,
            },
        )

    return registro


def avaliar_conquistas(
    perfil,
):
    from tarefas.models import TarefaAgendada

    aprovadas = (
        TarefaAgendada.objects
        .filter(
            crianca=perfil,
            status=(
                TarefaAgendada
                .Status
                .APROVADA
            ),
        )
        .count()
    )

    if aprovadas >= 1:
        _desbloquear_conquista(
            perfil=perfil,
            slug="primeira-missao",
        )

    if aprovadas >= 10:
        _desbloquear_conquista(
            perfil=perfil,
            slug="dez-missoes",
        )

    if aprovadas >= 30:
        _desbloquear_conquista(
            perfil=perfil,
            slug="trinta-missoes",
        )

    if calcular_sequencia(perfil) >= 7:
        _desbloquear_conquista(
            perfil=perfil,
            slug="sequencia-sete",
        )

    progressos = {
        item.habilidade.slug: item
        for item in (
            ProgressoHabilidade.objects
            .filter(
                crianca=perfil,
                habilidade__slug__in=[
                    "autonomia",
                    "organizacao",
                ],
            )
            .select_related(
                "habilidade"
            )
        )
    }

    autonomia = progressos.get(
        "autonomia"
    )

    if (
        autonomia
        and autonomia.nivel_atual >= 3
    ):
        _desbloquear_conquista(
            perfil=perfil,
            slug="autonomia-n3",
        )

    organizacao = progressos.get(
        "organizacao"
    )

    if (
        organizacao
        and organizacao.nivel_atual >= 3
    ):
        _desbloquear_conquista(
            perfil=perfil,
            slug="organizacao-n3",
        )
