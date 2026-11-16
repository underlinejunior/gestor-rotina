from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from gamificacao.models import (
    ConquistaInfantil,
    MovimentacaoPontos,
    MovimentacaoHabilidade,
)
from gamificacao.services import calcular_sequencia
from usuarios.models import PerfilInfantil, Usuario
from usuarios.views import obter_familia_tutor

from .models import TarefaAgendada, RotinaPlanejada


def _familia_do_tutor(request):
    return obter_familia_tutor(request.user)


def _calcular_idade(data_nascimento):
    if not data_nascimento:
        return None

    hoje = timezone.localdate()
    idade = hoje.year - data_nascimento.year

    if (
        (hoje.month, hoje.day)
        < (
            data_nascimento.month,
            data_nascimento.day,
        )
    ):
        idade -= 1

    return max(0, idade)


def _inicio_semana_relatorio(request):
    hoje = timezone.localdate()
    valor = (request.GET.get("inicio") or "").strip()

    if valor:
        try:
            inicio = datetime.strptime(
                valor,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            inicio = hoje
    else:
        inicio = hoje

    return inicio - timedelta(days=inicio.weekday())


def _ordem_momento_relatorio(periodo, horario=None):
    ordem = {
        "MANHA": 1,
        "TARDE": 2,
        "NOITE": 3,
        "HORARIO": 4,
        "QUALQUER": 5,
    }

    return (
        ordem.get(periodo, 6),
        horario or datetime.max.time(),
    )


def _celula_vazia():
    return {
        "programada": False,
        "simbolo": "—",
        "label": "Não programada",
        "classe": "not-planned",
    }


def _celula_programada():
    return {
        "programada": True,
        "simbolo": "□",
        "label": "A fazer",
        "classe": "pending",
    }


def _celula_tarefa(tarefa):
    mapa = {
        TarefaAgendada.Status.APROVADA: {
            "simbolo": "✓",
            "label": "Concluída",
            "classe": "approved",
        },
        TarefaAgendada.Status.REVISAO: {
            "simbolo": "⏳",
            "label": "Em revisão",
            "classe": "review",
        },
        TarefaAgendada.Status.NAO_REALIZADA: {
            "simbolo": "✕",
            "label": "Não realizada",
            "classe": "missed",
        },
        TarefaAgendada.Status.REJEITADA: {
            "simbolo": "□",
            "label": "Refazer",
            "classe": "pending",
        },
        TarefaAgendada.Status.PENDENTE: {
            "simbolo": "□",
            "label": "A fazer",
            "classe": "pending",
        },
    }

    dados = mapa.get(
        tarefa.status,
        {
            "simbolo": "□",
            "label": tarefa.get_status_display(),
            "classe": "pending",
        },
    )

    return {
        "programada": True,
        **dados,
    }


def _chave_tarefa(tarefa):
    if tarefa.rotina_id:
        return ("rotina", tarefa.rotina_id)

    if tarefa.origem == TarefaAgendada.Origem.BONUS:
        return ("bonus", tarefa.id)

    return (
        "historico",
        tarefa.titulo.strip().lower(),
        tarefa.periodo,
        tarefa.horario,
        tarefa.pontos_base,
    )


def _montar_quadro_semanal(
    *,
    rotinas,
    instancias,
    dias_datas,
):
    linhas = {}

    for rotina in rotinas:
        dias_programados = [
            indice
            for indice, data in enumerate(dias_datas)
            if rotina.deve_gerar_em(data)
        ]

        if not dias_programados:
            continue

        chave = ("rotina", rotina.id)
        celulas = [
            _celula_vazia()
            for _ in dias_datas
        ]

        for indice in dias_programados:
            celulas[indice] = _celula_programada()

        linhas[chave] = {
            "titulo": rotina.titulo,
            "momento": rotina.momento_resumo,
            "periodo": rotina.periodo,
            "horario": rotina.horario,
            "pontos": rotina.pontos_base,
            "bonus": False,
            "dias": celulas,
        }

    indice_por_data = {
        data: indice
        for indice, data in enumerate(dias_datas)
    }

    for tarefa in instancias:
        indice_dia = indice_por_data.get(
            tarefa.data_referencia
        )

        if indice_dia is None:
            continue

        chave = _chave_tarefa(tarefa)

        if chave not in linhas:
            linhas[chave] = {
                "titulo": tarefa.titulo,
                "momento": tarefa.momento_resumo,
                "periodo": tarefa.periodo,
                "horario": tarefa.horario,
                "pontos": tarefa.pontos_base,
                "bonus": (
                    tarefa.origem
                    == TarefaAgendada.Origem.BONUS
                ),
                "dias": [
                    _celula_vazia()
                    for _ in dias_datas
                ],
            }

        linhas[chave]["dias"][indice_dia] = (
            _celula_tarefa(tarefa)
        )

    resultado = list(linhas.values())

    resultado.sort(
        key=lambda item: (
            *_ordem_momento_relatorio(
                item["periodo"],
                item["horario"],
            ),
            item["titulo"].lower(),
        )
    )

    return resultado


def _limites_semana_datetime(inicio, fim):
    timezone_atual = timezone.get_current_timezone()

    inicio_dt = timezone.make_aware(
        datetime.combine(
            inicio,
            datetime.min.time(),
        ),
        timezone_atual,
    )

    fim_exclusivo_dt = timezone.make_aware(
        datetime.combine(
            fim + timedelta(days=1),
            datetime.min.time(),
        ),
        timezone_atual,
    )

    return inicio_dt, fim_exclusivo_dt


def _saldo_anterior(
    *,
    perfil,
    inicio_dt,
):
    ultimo_antes = (
        MovimentacaoPontos.objects
        .filter(
            crianca=perfil,
            criado_em__lt=inicio_dt,
        )
        .order_by(
            "-criado_em",
            "-id",
        )
        .first()
    )

    if ultimo_antes:
        return int(ultimo_antes.saldo_resultante)

    primeiro_depois = (
        MovimentacaoPontos.objects
        .filter(
            crianca=perfil,
            criado_em__gte=inicio_dt,
        )
        .order_by(
            "criado_em",
            "id",
        )
        .first()
    )

    if primeiro_depois:
        return int(
            primeiro_depois.saldo_resultante
            - primeiro_depois.pontos
        )

    return int(perfil.saldo_pontos or 0)


@login_required(login_url="login")
def relatorio_semanal_crianca(
    request,
    perfil_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(request)

    perfil = get_object_or_404(
        PerfilInfantil,
        id=perfil_id,
        familia=familia,
    )

    inicio = _inicio_semana_relatorio(request)
    fim = inicio + timedelta(days=6)
    hoje = timezone.localdate()

    dias_datas = [
        inicio + timedelta(days=indice)
        for indice in range(7)
    ]

    nomes_dias = [
        "Seg",
        "Ter",
        "Qua",
        "Qui",
        "Sex",
        "Sáb",
        "Dom",
    ]

    cabecalho_dias = [
        {
            "nome": nomes_dias[indice],
            "data": data,
            "hoje": data == hoje,
        }
        for indice, data in enumerate(dias_datas)
    ]

    rotinas = list(
        RotinaPlanejada.objects
        .filter(
            crianca=perfil,
            ativa=True,
        )
        .order_by(
            "titulo"
        )
    )

    instancias = list(
        TarefaAgendada.objects
        .filter(
            crianca=perfil,
            data_referencia__gte=inicio,
            data_referencia__lte=fim,
        )
        .select_related(
            "rotina"
        )
        .order_by(
            "data_referencia",
            "criada_em",
        )
    )

    linhas_quadro = _montar_quadro_semanal(
        rotinas=rotinas,
        instancias=instancias,
        dias_datas=dias_datas,
    )

    total_planejado = sum(
        1
        for linha in linhas_quadro
        for celula in linha["dias"]
        if celula["programada"]
    )

    aprovadas = sum(
        1
        for tarefa in instancias
        if tarefa.status
        == TarefaAgendada.Status.APROVADA
    )

    nao_realizadas = sum(
        1
        for tarefa in instancias
        if tarefa.status
        == TarefaAgendada.Status.NAO_REALIZADA
    )

    em_revisao = sum(
        1
        for tarefa in instancias
        if tarefa.status
        == TarefaAgendada.Status.REVISAO
    )

    pendentes = sum(
        1
        for tarefa in instancias
        if tarefa.status in {
            TarefaAgendada.Status.PENDENTE,
            TarefaAgendada.Status.REJEITADA,
        }
    )

    finalizadas = aprovadas + nao_realizadas

    taxa_conclusao = (
        round(
            aprovadas
            / finalizadas
            * 100
        )
        if finalizadas
        else 0
    )

    inicio_dt, fim_exclusivo_dt = (
        _limites_semana_datetime(
            inicio,
            fim,
        )
    )

    movimentos_semana = list(
        MovimentacaoPontos.objects
        .filter(
            crianca=perfil,
            criado_em__gte=inicio_dt,
            criado_em__lt=fim_exclusivo_dt,
        )
        .select_related(
            "tarefa"
        )
        .order_by(
            "criado_em",
            "id",
        )
    )

    saldo_anterior = _saldo_anterior(
        perfil=perfil,
        inicio_dt=inicio_dt,
    )

    pontos_ganhos = sum(
        max(0, int(movimento.pontos))
        for movimento in movimentos_semana
        if movimento.tipo
        == MovimentacaoPontos.Tipo.APROVACAO
    )

    penalidades = abs(
        sum(
            min(0, int(movimento.pontos))
            for movimento in movimentos_semana
            if movimento.tipo
            == MovimentacaoPontos.Tipo.PENALIDADE
        )
    )

    resgates = abs(
        sum(
            min(0, int(movimento.pontos))
            for movimento in movimentos_semana
            if movimento.tipo
            == MovimentacaoPontos.Tipo.RESGATE
        )
    )

    ajustes = sum(
        int(movimento.pontos)
        for movimento in movimentos_semana
        if movimento.tipo
        == MovimentacaoPontos.Tipo.AJUSTE
    )

    saldo_final = (
        int(movimentos_semana[-1].saldo_resultante)
        if movimentos_semana
        else saldo_anterior
    )

    skills_semana = list(
        MovimentacaoHabilidade.objects
        .filter(
            crianca=perfil,
            tarefa__data_referencia__gte=inicio,
            tarefa__data_referencia__lte=fim,
        )
        .values(
            "habilidade__nome",
            "habilidade__icone",
        )
        .annotate(
            xp=Sum("xp")
        )
        .order_by(
            "-xp",
            "habilidade__nome",
        )[:8]
    )

    conquistas_ate_agora = (
        ConquistaInfantil.objects
        .filter(
            crianca=perfil,
            desbloqueada_em__lt=fim_exclusivo_dt,
        )
        .select_related(
            "conquista"
        )
        .order_by(
            "conquista__ordem",
            "desbloqueada_em",
        )
    )

    ultimas_penalidades = (
        MovimentacaoPontos.objects
        .filter(
            crianca=perfil,
            tipo=MovimentacaoPontos.Tipo.PENALIDADE,
            tarefa__isnull=False,
            criado_em__lt=fim_exclusivo_dt,
        )
        .select_related(
            "tarefa"
        )
        .order_by(
            "-criado_em",
            "-id",
        )[:5]
    )

    contexto = {
        "perfil": perfil,
        "familia": familia,
        "idade": _calcular_idade(
            perfil.data_nascimento
        ),
        "inicio": inicio,
        "fim": fim,
        "inicio_anterior": inicio - timedelta(days=7),
        "inicio_proxima": inicio + timedelta(days=7),
        "inicio_atual": (
            hoje
            - timedelta(days=hoje.weekday())
        ),
        "cabecalho_dias": cabecalho_dias,
        "linhas_quadro": linhas_quadro,
        "total_planejado": total_planejado,
        "aprovadas": aprovadas,
        "nao_realizadas": nao_realizadas,
        "em_revisao": em_revisao,
        "pendentes": pendentes,
        "taxa_conclusao": taxa_conclusao,
        "pontos_ganhos": pontos_ganhos,
        "penalidades": penalidades,
        "resgates": resgates,
        "ajustes": ajustes,
        "saldo_anterior": saldo_anterior,
        "saldo_final": saldo_final,
        "skills_semana": skills_semana,
        "conquistas_ate_agora": conquistas_ate_agora,
        "ultimas_penalidades": ultimas_penalidades,
        "sequencia_atual": calcular_sequencia(
            perfil
        ),
        "gerado_em": timezone.localtime(),
        "responsaveis": (
            familia.tutores.all()
            .order_by(
                "first_name",
                "username",
            )
        ),
    }

    return render(
        request,
        "tarefas/relatorios/semanal.html",
        contexto,
    )
