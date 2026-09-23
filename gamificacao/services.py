from datetime import timedelta
import math

from django.db import transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilCrianca, Usuario

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
    dados_nivel_skill,
)


@transaction.atomic
def registrar_pontos_aprovacao(
    tarefa,
    tutor,
    pontos,
):
    if MovimentoPontos.objects.filter(
        tarefa=tarefa
    ).exists():
        raise ValueError(
            "Esta tarefa já possui movimentação de pontos."
        )

    perfil = (
        PerfilCrianca.objects
        .select_for_update()
        .get(pk=tarefa.crianca_id)
    )

    nivel_antes = perfil.avatar_nivel
    pontos = max(0, int(pontos))

    # Perfis antigos ainda podem ter XP histórico zerado.
    # Antes de creditar novos pontos, preservamos o maior saldo
    # positivo já conhecido como base histórica.
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

    movimento = MovimentoPontos.objects.create(
        crianca=perfil,
        tarefa=tarefa,
        tipo=MovimentoPontos.Tipo.APROVACAO,
        pontos=pontos,
        saldo_apos=perfil.saldo_pontos,
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


def salvar_skills_molde(
    molde,
    impactos,
):
    MoldeTarefaSkill.objects.filter(
        molde=molde
    ).delete()

    novos = []

    for skill_id, impacto in impactos.items():
        if impacto not in {
            Skill.Impacto.LEVE,
            Skill.Impacto.MEDIO,
            Skill.Impacto.FORTE,
        }:
            continue

        novos.append(
            MoldeTarefaSkill(
                molde=molde,
                skill_id=skill_id,
                impacto=impacto,
            )
        )

    if novos:
        MoldeTarefaSkill.objects.bulk_create(
            novos
        )


def copiar_skills_molde_para_tarefa(
    molde,
    tarefa,
):
    if tarefa.skills_snapshot.exists():
        return

    associacoes = (
        MoldeTarefaSkill.objects
        .filter(molde=molde)
        .select_related("skill")
    )

    snapshots = []

    for associacao in associacoes:
        snapshots.append(
            InstanciaTarefaSkill(
                tarefa=tarefa,
                skill=associacao.skill,
                nome_snapshot=associacao.skill.nome,
                icone_snapshot=associacao.skill.icone,
                impacto=associacao.impacto,
                xp_planejado=Skill.xp_por_impacto(
                    associacao.impacto
                ),
            )
        )

    if snapshots:
        InstanciaTarefaSkill.objects.bulk_create(
            snapshots
        )


def salvar_skills_tarefa_bonus(
    tarefa,
    impactos,
):
    snapshots = []

    skills = {
        skill.id: skill
        for skill in Skill.objects.filter(
            id__in=impactos.keys(),
            ativa=True,
        )
    }

    for skill_id, impacto in impactos.items():
        skill = skills.get(int(skill_id))

        if not skill:
            continue

        if impacto not in {
            Skill.Impacto.LEVE,
            Skill.Impacto.MEDIO,
            Skill.Impacto.FORTE,
        }:
            continue

        snapshots.append(
            InstanciaTarefaSkill(
                tarefa=tarefa,
                skill=skill,
                nome_snapshot=skill.nome,
                icone_snapshot=skill.icone,
                impacto=impacto,
                xp_planejado=Skill.xp_por_impacto(
                    impacto
                ),
            )
        )

    if snapshots:
        InstanciaTarefaSkill.objects.bulk_create(
            snapshots
        )


@transaction.atomic
def registrar_xp_skills_aprovacao(
    tarefa,
):
    snapshots = list(
        tarefa
        .skills_snapshot
        .select_related("skill")
        .all()
    )

    evolucoes = []

    for snapshot in snapshots:
        if MovimentoSkill.objects.filter(
            tarefa=tarefa,
            skill=snapshot.skill,
        ).exists():
            continue

        progresso, _ = (
            ProgressoSkill.objects
            .select_for_update()
            .get_or_create(
                crianca=tarefa.crianca,
                skill=snapshot.skill,
                defaults={"xp_total": 0},
            )
        )

        nivel_antes = progresso.nivel_atual

        progresso.xp_total += snapshot.xp_planejado
        progresso.save(
            update_fields=[
                "xp_total",
                "atualizado_em",
            ]
        )

        nivel_depois = progresso.nivel_atual

        movimento = MovimentoSkill.objects.create(
            crianca=tarefa.crianca,
            skill=snapshot.skill,
            tarefa=tarefa,
            xp=snapshot.xp_planejado,
            nivel_antes=nivel_antes,
            nivel_depois=nivel_depois,
        )

        if nivel_depois > nivel_antes:
            evolucoes.append(
                {
                    "skill": snapshot.skill,
                    "movimento": movimento,
                    "nivel_antes": nivel_antes,
                    "nivel_depois": nivel_depois,
                    "titulo_novo": dados_nivel_skill(
                        progresso.xp_total
                    )["titulo"],
                }
            )

            criar_notificacoes_evolucao_skill(
                perfil=tarefa.crianca,
                skill=snapshot.skill,
                movimento=movimento,
                nivel_antes=nivel_antes,
                nivel_depois=nivel_depois,
            )

    return evolucoes


def criar_notificacoes_evolucao_skill(
    *,
    perfil,
    skill,
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
                f"{skill.icone} {skill.nome} evoluiu!"
            )
            mensagem = (
                f"Sua habilidade {skill.nome} avançou do nível "
                f"{nivel_antes} para o nível {nivel_depois}."
            )
            url_destino = reverse(
                "minhas_habilidades"
            )
        else:
            titulo = (
                f"{skill.icone} {skill.nome} de "
                f"{perfil.nome_exibicao} evoluiu"
            )
            mensagem = (
                f"A prática de atividades ligadas a {skill.nome} "
                f"avançou do nível {nivel_antes} para "
                f"o nível {nivel_depois}."
            )
            url_destino = reverse(
                "habilidades_crianca_tutor",
                args=[perfil.id],
            )

        NotificacaoSistema.objects.get_or_create(
            usuario_destino=usuario,
            chave=f"skill:{movimento.id}:{usuario.id}",
            defaults={
                "crianca": perfil,
                "skill": skill,
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
        Skill.objects
        .filter(ativa=True)
        .order_by("ordem", "nome")
    )

    progressos = {
        item.skill_id: item
        for item in (
            ProgressoSkill.objects
            .filter(
                crianca=perfil,
                skill__in=skills,
            )
            .select_related("skill")
        )
    }

    inicio_recente = (
        timezone.now()
        - timedelta(days=30)
    )

    recentes = {
        item["skill_id"]: (
            item["total"] or 0
        )
        for item in (
            MovimentoSkill.objects
            .filter(
                crianca=perfil,
                skill__in=skills,
                criado_em__gte=inicio_recente,
            )
            .values("skill_id")
            .annotate(total=Sum("xp"))
        )
    }

    painel = []

    for skill in skills:
        progresso = progressos.get(
            skill.id
        )

        xp_total = (
            progresso.xp_total
            if progresso
            else 0
        )

        dados = dados_nivel_skill(
            xp_total
        )

        xp_recente = recentes.get(
            skill.id,
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

        painel.append(
            {
                "skill": skill,
                "xp_total": xp_total,
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
        MovimentoPontos.objects
        .filter(tarefa=tarefa)
        .first()
    )

    if movimento_existente:
        return movimento_existente

    perfil = (
        PerfilCrianca.objects
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

    # Preserva a experiência histórica antes de aplicar
    # a penalidade ao saldo disponível.
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

    return MovimentoPontos.objects.create(
        crianca=perfil,
        tarefa=tarefa,
        tipo=MovimentoPontos.Tipo.PENALIDADE,
        pontos=-penalidade,
        saldo_apos=perfil.saldo_pontos,
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
    from tarefas.models import InstanciaTarefa

    ontem = hoje - timedelta(days=1)

    tarefas_ontem = InstanciaTarefa.objects.filter(
        familia=familia,
        data_referencia=ontem,
    )

    if tarefas_ontem.exists():
        aprovadas = tarefas_ontem.filter(
            status=InstanciaTarefa.Status.APROVADA
        ).count()

        nao_realizadas = tarefas_ontem.filter(
            status=InstanciaTarefa.Status.NAO_REALIZADA
        ).count()

        revisao = tarefas_ontem.filter(
            status=InstanciaTarefa.Status.REVISAO
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

    tarefas_semana = InstanciaTarefa.objects.filter(
        familia=familia,
        data_referencia__gte=inicio,
        data_referencia__lte=fim,
    )

    if not tarefas_semana.exists():
        return

    aprovadas = tarefas_semana.filter(
        status=InstanciaTarefa.Status.APROVADA
    ).count()

    nao_realizadas = tarefas_semana.filter(
        status=InstanciaTarefa.Status.NAO_REALIZADA
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
):
    perfil = (
        PerfilCrianca.objects
        .select_for_update()
        .get(pk=perfil.pk)
    )

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

    # Preserva o nível do avatar antes de gastar o saldo.
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

    movimento = MovimentoPontos.objects.create(
        crianca=perfil,
        tarefa=None,
        tipo=MovimentoPontos.Tipo.RESGATE,
        pontos=-recompensa.custo_pontos,
        saldo_apos=perfil.saldo_pontos,
        nivel_antes=perfil.avatar_nivel,
        nivel_depois=perfil.avatar_nivel,
        registrado_por=None,
    )

    resgate = ResgateRecompensa.objects.create(
        crianca=perfil,
        recompensa=recompensa,
        titulo_snapshot=recompensa.titulo,
        icone_snapshot=recompensa.icone,
        custo_snapshot=recompensa.custo_pontos,
        movimento_pontos=movimento,
    )

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
def cancelar_resgate(
    *,
    resgate,
    tutor,
):
    if (
        resgate.status
        != ResgateRecompensa
        .Status
        .SOLICITADO
    ):
        raise ValueError(
            "Apenas resgates pendentes podem ser cancelados."
        )

    perfil = (
        PerfilCrianca.objects
        .select_for_update()
        .get(pk=resgate.crianca_id)
    )

    perfil.saldo_pontos += resgate.custo_snapshot

    perfil.save(
        update_fields=[
            "saldo_pontos",
        ]
    )

    MovimentoPontos.objects.create(
        crianca=perfil,
        tarefa=None,
        tipo=MovimentoPontos.Tipo.AJUSTE,
        pontos=resgate.custo_snapshot,
        saldo_apos=perfil.saldo_pontos,
        nivel_antes=perfil.avatar_nivel,
        nivel_depois=perfil.avatar_nivel,
        registrado_por=tutor,
    )

    resgate.status = (
        ResgateRecompensa
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
    from tarefas.models import InstanciaTarefa

    hoje = timezone.localdate()

    inicio = (
        hoje
        - timedelta(
            days=limite_dias
        )
    )

    tarefas = list(
        InstanciaTarefa.objects
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
    from tarefas.models import InstanciaTarefa

    hoje = timezone.localdate()

    inicio = (
        hoje
        - timedelta(
            days=limite_dias
        )
    )

    tarefas = (
        InstanciaTarefa.objects
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
        ConquistaCrianca.objects
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
    from tarefas.models import InstanciaTarefa

    aprovadas = (
        InstanciaTarefa.objects
        .filter(
            crianca=perfil,
            status=(
                InstanciaTarefa
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
        item.skill.slug: item
        for item in (
            ProgressoSkill.objects
            .filter(
                crianca=perfil,
                skill__slug__in=[
                    "autonomia",
                    "organizacao",
                ],
            )
            .select_related(
                "skill"
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
