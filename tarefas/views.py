from datetime import timedelta
import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import FileResponse, JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import (
    require_GET,
    require_POST,
)

from gamificacao.catalogo import carregar_catalogo_padrao

from gamificacao.models import (
    MoldeTarefaSkill,
    MovimentoPontos,
    ProgressoSkill,
    Skill,
)
from gamificacao.services import (
    salvar_skills_molde,
    salvar_skills_tarefa_bonus,
)
from usuarios.models import PerfilCrianca, Usuario
from usuarios.views import obter_familia_tutor

from .forms import (
    EnvioComprovanteForm,
    MoldeTarefaForm,
    RevisaoTarefaForm,
    TarefaBonusForm,
)
from .models import (
    InstanciaTarefa,
    MoldeTarefa,
    SugestaoTarefa,
)
from .services import (
    ConfiguracaoIAAusente,
    DependenciaIAAusente,
    ErroSugestaoIA,
    aprovar_tarefa,
    calcular_indicadores_periodo,
    enviar_comprovante,
    gerar_sugestao_rotina,
    processar_rotinas,
    rejeitar_tarefa,
)

PERIODOS_HISTORICO = {
    7,
    30,
    90,
}


def _familia_do_tutor(request):
    return obter_familia_tutor(
        request.user
    )


def _pode_operar_tarefa(
    request,
    tarefa,
):
    if request.user.tipo == Usuario.Tipo.CRIANCA:
        perfil = getattr(
            request.user,
            "perfil_crianca",
            None,
        )

        return (
            perfil is not None
            and tarefa.crianca_id == perfil.id
        )

    if request.user.tipo == Usuario.Tipo.TUTOR:
        familia = _familia_do_tutor(
            request
        )

        return tarefa.familia_id == familia.id

    return False


def _periodo_solicitado(
    request,
):
    try:
        periodo = int(
            request.GET.get(
                "periodo",
                30,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        periodo = 30

    if periodo not in PERIODOS_HISTORICO:
        periodo = 30

    return periodo


def _calcular_idade(
    data_nascimento,
):
    if not data_nascimento:
        return None

    hoje = timezone.localdate()

    idade = (
        hoje.year
        - data_nascimento.year
    )

    if (
        (hoje.month, hoje.day)
        < (
            data_nascimento.month,
            data_nascimento.day,
        )
    ):
        idade -= 1

    return max(
        0,
        idade,
    )


def _slugs_enfase_solicitados(request, skills_ativas):
    """Retorna até três Skills escolhidas manualmente como ênfase."""
    valor = (request.GET.get("enfase", "auto") or "auto").strip().lower()
    if not valor or valor == "auto":
        return []

    validos = {skill.slug for skill in skills_ativas}
    resultado = []
    for slug in valor.split(","):
        slug = slug.strip()
        if slug in validos and slug not in resultado:
            resultado.append(slug)
        if len(resultado) >= 3:
            break
    return resultado


def _diagnostico_skills_crianca(perfil, skills_ativas=None):
    """Cruza evolução real e distribuição das Skills nas rotinas ativas."""
    skills_ativas = list(
        skills_ativas
        or Skill.objects.filter(ativa=True).order_by("ordem", "nome")
    )

    progressos = {
        item.skill_id: item
        for item in ProgressoSkill.objects.filter(
            crianca=perfil,
            skill__in=skills_ativas,
        ).select_related("skill")
    }

    cobertura = {
        skill.id: {"rotinas": set(), "carga": 0}
        for skill in skills_ativas
    }

    associacoes = (
        MoldeTarefaSkill.objects
        .filter(
            molde__crianca=perfil,
            molde__ativa=True,
            skill__in=skills_ativas,
        )
        .select_related("skill", "molde")
    )

    for associacao in associacoes:
        item = cobertura.setdefault(
            associacao.skill_id,
            {"rotinas": set(), "carga": 0},
        )
        item["rotinas"].add(associacao.molde_id)
        item["carga"] += int(associacao.impacto or 0)

    valores_xp = [
        int(progressos.get(skill.id).xp_total)
        if progressos.get(skill.id) else 0
        for skill in skills_ativas
    ]
    valores_carga = [
        int(cobertura.get(skill.id, {}).get("carga", 0))
        for skill in skills_ativas
    ]

    max_xp = max(valores_xp, default=0)
    min_xp = min(valores_xp, default=0)
    max_carga = max(valores_carga, default=0)
    media_carga = (
        sum(valores_carga) / len(valores_carga)
        if valores_carga else 0
    )

    repetidas_ids = set()
    if media_carga > 0:
        limite_repeticao = max(4.0, media_carga * 1.65)
        repetidas_ids = {
            skill.id
            for skill in skills_ativas
            if cobertura.get(skill.id, {}).get("carga", 0) >= limite_repeticao
        }

    itens = []
    for skill in skills_ativas:
        progresso = progressos.get(skill.id)
        xp = int(progresso.xp_total) if progresso else 0
        info_cobertura = cobertura.get(skill.id, {"rotinas": set(), "carga": 0})
        rotinas_ativas = len(info_cobertura["rotinas"])
        carga = int(info_cobertura["carga"])


        lacuna_xp = 1.0 if max_xp == 0 else 1.0 - (xp / max_xp)
        lacuna_cobertura = 1.0 if max_carga == 0 else 1.0 - (carga / max_carga)
        prioridade = round((lacuna_xp * 0.62 + lacuna_cobertura * 0.38) * 100)

        if carga == 0:
            motivo = "Ainda não aparece nas rotinas ativas"
        elif max_xp > min_xp and xp == min_xp:
            motivo = "Está entre as habilidades menos desenvolvidas"
        elif skill.id in repetidas_ids:
            motivo = "Já aparece com muita frequência nas rotinas"
        else:
            motivo = "Participação equilibrada nas rotinas"

        itens.append({
            "id": skill.id,
            "slug": skill.slug,
            "nome": skill.nome,
            "icone": skill.icone,
            "xp": xp,
            "nivel": progresso.nivel_atual if progresso else 1,
            "rotinas_ativas": rotinas_ativas,
            "carga": carga,
            "prioridade": prioridade,
            "repetida": skill.id in repetidas_ids,
            "motivo": motivo,
        })

    tem_dados = max_xp > 0 or max_carga > 0

    recomendadas = (
        sorted(
            [item for item in itens if not item["repetida"]],
            key=lambda item: (
                -item["prioridade"],
                item["carga"],
                item["xp"],
                item["nome"],
            ),
        )[:3]
        if tem_dados
        else []
    )

    repetidas = sorted(
        [item for item in itens if item["repetida"]],
        key=lambda item: (-item["carga"], item["nome"]),
    )[:3]

    if not tem_dados:
        resumo = (
            "Ainda não há histórico suficiente para apontar lacunas. "
            "As sugestões serão organizadas principalmente pela idade."
        )
    elif recomendadas:
        nomes = ", ".join(item["nome"] for item in recomendadas[:2])
        resumo = f"Para equilibrar a rotina, vale priorizar {nomes}."
    else:
        resumo = "As habilidades estão bem distribuídas nas rotinas atuais."

    if repetidas:
        nomes = ", ".join(item["nome"] for item in repetidas[:2])
        resumo += f" {nomes} já aparece bastante nas tarefas cadastradas."

    return {
        "skills": itens,
        "recomendadas": recomendadas,
        "repetidas": repetidas,
        "resumo": resumo,
    }


def _pontuar_sugestao_por_skills(sugestao, slugs_alvo, slugs_repetidas):
    impactos = {
        item.skill.slug: int(item.impacto or 0)
        for item in sugestao.skills_associadas.all()
    }

    pontos = 0
    for indice, slug in enumerate(slugs_alvo):
        impacto = impactos.get(slug, 0)
        if impacto:
            pontos += impacto * max(18, 54 - indice * 12)

    for slug in slugs_repetidas:
        if slug in slugs_alvo:
            continue
        impacto = impactos.get(slug, 0)
        if impacto:
            pontos -= impacto * 12

    return pontos


@login_required(login_url="login")
@require_GET
def api_sugerir_rotina(request):
    """Gera sugestões de IA considerando evolução, cobertura e ênfase."""
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return JsonResponse(
            {"erro": "Apenas Tutores podem gerar sugestões."},
            status=403,
        )

    familia = _familia_do_tutor(request)

    try:
        perfil_id = int(request.GET.get("crianca_id", 0))
    except (TypeError, ValueError):
        perfil_id = 0

    if not perfil_id:
        return JsonResponse(
            {"erro": "Selecione uma criança para gerar sugestões."},
            status=400,
        )

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    idade = _calcular_idade(perfil.data_nascimento)
    idade_consulta = idade if idade is not None else 8

    contexto = (
        request.GET.get("contexto", "rotina diária")
        or "rotina diária"
    ).strip()[:120]

    skills_ativas = list(
        Skill.objects
        .filter(ativa=True)
        .order_by("ordem", "nome")
    )
    diagnostico = _diagnostico_skills_crianca(
        perfil,
        skills_ativas=skills_ativas,
    )
    slugs_enfase = _slugs_enfase_solicitados(request, skills_ativas)

    skills_prompt = [
        {
            "slug": skill.slug,
            "nome": skill.nome,
            "descricao": skill.descricao,
        }
        for skill in skills_ativas
    ]

    titulos_existentes = list(
        MoldeTarefa.objects
        .filter(crianca=perfil, ativa=True)
        .values_list("titulo", flat=True)
    )

    try:
        sugestoes_ia = gerar_sugestao_rotina(
            idade_consulta,
            contexto,
            skills_validas=skills_prompt,
            diagnostico_skills=diagnostico,
            skills_enfase=slugs_enfase,
            titulos_existentes=titulos_existentes,
        )
    except (
        ConfiguracaoIAAusente,
        DependenciaIAAusente,
    ) as exc:
        return JsonResponse(
            {"erro": str(exc)},
            status=503,
        )
    except ErroSugestaoIA:
        return JsonResponse(
            {
                "erro": (
                    "As sugestões com IA estão temporariamente indisponíveis. "
                    "Você pode escolher uma tarefa do sistema ou criar a sua."
                )
            },
            status=503,
        )

    skills_por_slug = {
        skill.slug: skill
        for skill in skills_ativas
    }

    sugestoes = []

    for indice, item in enumerate(sugestoes_ia[:6], start=1):
        skills = []

        for associacao in item.get("skills", []):
            skill = skills_por_slug.get(associacao.get("slug"))
            if skill is None:
                continue

            skills.append({
                "id": skill.id,
                "slug": skill.slug,
                "nome": skill.nome,
                "icone": skill.icone,
                "impacto": associacao.get("impacto", 0),
                "simbolo": Skill.simbolo_impacto(
                    associacao.get("impacto", 0)
                ),
            })

        if not skills:
            continue

        sugestoes.append({
            "id": f"ia-{indice}",
            "origem": "ia",
            "icone": item.get("icone") or "✨",
            "titulo": item.get("titulo", ""),
            "descricao": item.get("descricao", ""),
            "pontos": item.get("pontos", 10),
            "skills": skills,
        })

    if not sugestoes:
        return JsonResponse(
            {"erro": "A IA não retornou sugestões utilizáveis."},
            status=503,
        )

    return JsonResponse(
        {
            "crianca": perfil.nome_exibicao,
            "idade": idade,
            "modo_enfase": "manual" if slugs_enfase else "automatico",
            "skills_enfase": slugs_enfase,
            "diagnostico": diagnostico,
            "sugestoes": sugestoes,
        }
    )


def _skills_para_formulario(
    request,
    molde=None,
):
    impactos = {}

    if request.method == "POST":
        for skill in Skill.objects.filter(
            ativa=True
        ):
            chave = (
                f"skill_impact_"
                f"{skill.id}"
            )

            try:
                valor = int(
                    request.POST.get(
                        chave,
                        0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                valor = 0

            impactos[
                skill.id
            ] = valor

    elif molde is not None:
        impactos = {
            item.skill_id: item.impacto
            for item in (
                MoldeTarefaSkill.objects
                .filter(
                    molde=molde
                )
            )
        }

    return [
        {
            "skill": skill,
            "impacto": impactos.get(
                skill.id,
                0,
            ),
        }
        for skill in (
            Skill.objects
            .filter(ativa=True)
            .order_by(
                "ordem",
                "nome",
            )
        )
    ]


def _garantir_catalogo_sugestoes():
    """
    Garante que o catálogo básico exista mesmo quando o usuário
    aplicou arquivos novos sem executar novamente o post_migrate.
    """
    if (
        not SugestaoTarefa.objects.filter(
            ativa=True
        ).exists()
        or not Skill.objects.filter(
            ativa=True
        ).exists()
    ):
        carregar_catalogo_padrao()


def _serializar_sugestao(
    sugestao,
):
    return {
        "id": sugestao.id,
        "origem": "sistema",
        "icone": sugestao.icone,
        "titulo": sugestao.titulo,
        "descricao": sugestao.descricao,
        "categoria": sugestao.categoria,
        "categoria_label": (
            sugestao.get_categoria_display()
        ),
        "pontos": sugestao.pontos_sugeridos,
        "frequencia": sugestao.frequencia_sugerida,
        "dias_semana": sugestao.dias_semana_lista,
        "skills": [
            {
                "id": item.skill.id,
                "slug": item.skill.slug,
                "nome": item.skill.nome,
                "icone": item.skill.icone,
                "impacto": item.impacto,
                "simbolo": (
                    Skill.simbolo_impacto(
                        item.impacto
                    )
                ),
            }
            for item in (
                sugestao
                .skills_associadas
                .all()
            )
        ],
    }


def _sugestoes_basicas(
    limite=6,
):
    _garantir_catalogo_sugestoes()

    sugestoes = (
        SugestaoTarefa.objects
        .filter(ativa=True)
        .filter(
            idade_minima__lte=8,
            idade_maxima__gte=8,
        )
        .prefetch_related(
            "skills_associadas__skill"
        )
        .order_by(
            "ordem",
            "titulo",
        )[:limite]
    )

    return [
        _serializar_sugestao(
            sugestao
        )
        for sugestao in sugestoes
    ]


def _render_historico(
    request,
    perfil,
):
    periodo = _periodo_solicitado(
        request
    )

    hoje = timezone.localdate()

    processar_rotinas(
        familia=perfil.familia,
        data=hoje,
    )

    inicio = (
        hoje
        - timedelta(
            days=periodo - 1
        )
    )

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            crianca=perfil,
            data_referencia__gte=inicio,
            data_referencia__lte=hoje,
        )
        .prefetch_related(
            "skills_snapshot"
        )
        .order_by(
            "-data_referencia",
            "-criada_em",
        )
    )

    indicadores = (
        calcular_indicadores_periodo(
            perfil=perfil,
            dias=periodo,
        )
    )

    movimentos = (
        MovimentoPontos.objects
        .filter(
            crianca=perfil,
            criado_em__date__gte=inicio,
            criado_em__date__lte=hoje,
        )
        .select_related("tarefa")
        .order_by("-criado_em")
    )

    pontos_periodo = (
        movimentos.aggregate(
            total=Sum("pontos")
        )["total"]
        or 0
    )

    return render(
        request,
        "tarefas/historico.html",
        {
            "perfil": perfil,
            "periodo": periodo,
            "tarefas": tarefas,
            "indicadores": indicadores,
            "movimentos": movimentos[:20],
            "pontos_periodo": pontos_periodo,
        },
    )


@login_required(login_url="login")
def rotinas_listar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    moldes = (
        MoldeTarefa.objects
        .filter(familia=familia)
        .select_related("crianca")
        .prefetch_related(
            "skills_associadas__skill"
        )
        .order_by(
            "crianca__nome",
            "titulo",
        )
    )

    return render(
        request,
        "tarefas/rotinas/lista.html",
        {
            "moldes": moldes,
        },
    )


@login_required(login_url="login")
def rotina_criar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    _garantir_catalogo_sugestoes()

    familia = _familia_do_tutor(
        request
    )

    if request.method == "POST":
        form = MoldeTarefaForm(
            request.POST,
            familia=familia,
        )

        if form.is_valid():
            molde_base = form.save(
                commit=False
            )

            molde_base.familia = familia
            molde_base.criado_por = request.user
            molde_base.save()

            impactos = (
                form.obter_impactos_skills()
            )

            salvar_skills_molde(
                molde_base,
                impactos,
            )

            moldes_criados = [
                molde_base
            ]

            if form.cleaned_data.get(
                "replicar_todas",
                False,
            ):
                outras_criancas = (
                    PerfilCrianca.objects
                    .filter(
                        familia=familia
                    )
                    .exclude(
                        pk=molde_base.crianca_id
                    )
                    .order_by("nome")
                )

                for crianca in outras_criancas:
                    molde = (
                        MoldeTarefa.objects
                        .create(
                            familia=familia,
                            crianca=crianca,
                            titulo=molde_base.titulo,
                            descricao=molde_base.descricao,
                            pontos_base=(
                                molde_base.pontos_base
                            ),
                            frequencia=(
                                molde_base.frequencia
                            ),
                            dias_semana=(
                                molde_base.dias_semana
                            ),
                            periodo=(
                                molde_base.periodo
                            ),
                            horario=(
                                molde_base.horario
                            ),
                            lembrete_ativo=(
                                molde_base.lembrete_ativo
                            ),
                            ativa=molde_base.ativa,
                            criado_por=request.user,
                        )
                    )

                    salvar_skills_molde(
                        molde,
                        impactos,
                    )

                    moldes_criados.append(
                        molde
                    )

            if len(moldes_criados) > 1:
                messages.success(
                    request,
                    (
                        "Rotina criada e replicada para "
                        f"{len(moldes_criados)} crianças!"
                    ),
                )
            else:
                messages.success(
                    request,
                    "Rotina criada com sucesso!",
                )

            processar_rotinas(
                familia=familia
            )

            return redirect(
                "rotinas_listar"
            )
    else:
        form = MoldeTarefaForm(
            familia=familia
        )

    return render(
        request,
        "tarefas/rotinas/form.html",
        {
            "form": form,
            "titulo": "Nova rotina",
            "texto_botao": "Criar rotina",
            "skills_disponiveis": (
                _skills_para_formulario(
                    request
                )
            ),
            "sugestoes_iniciais": (
                _sugestoes_basicas(
                    limite=6
                )
            ),
        },
    )


@login_required(login_url="login")
def rotina_editar(
    request,
    molde_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    molde = get_object_or_404(
        MoldeTarefa,
        id=molde_id,
        familia=familia,
    )

    if request.method == "POST":
        form = MoldeTarefaForm(
            request.POST,
            instance=molde,
            familia=familia,
            permitir_replicacao=False,
        )

        if form.is_valid():
            form.save()

            salvar_skills_molde(
                molde,
                form.obter_impactos_skills(),
            )

            messages.success(
                request,
                (
                    "Rotina atualizada com sucesso! "
                    "As tarefas históricas preservam "
                    "as habilidades originais."
                ),
            )

            processar_rotinas(
                familia=familia
            )

            return redirect(
                "rotinas_listar"
            )
    else:
        form = MoldeTarefaForm(
            instance=molde,
            familia=familia,
            permitir_replicacao=False,
        )

    return render(
        request,
        "tarefas/rotinas/form.html",
        {
            "form": form,
            "titulo": "Editar rotina",
            "texto_botao": "Salvar alterações",
            "skills_disponiveis": (
                _skills_para_formulario(
                    request,
                    molde=molde,
                )
            ),
        },
    )


@login_required(login_url="login")
@require_GET
def sugestoes_tarefas(request):
    """Sugestões do catálogo, ordenadas pelo equilíbrio de Skills da criança."""
    _garantir_catalogo_sugestoes()

    if request.user.tipo != Usuario.Tipo.TUTOR:
        return JsonResponse(
            {"erro": "Apenas Tutores podem consultar sugestões."},
            status=403,
        )

    familia = _familia_do_tutor(request)

    try:
        perfil_id = int(request.GET.get("crianca_id", 0))
    except (TypeError, ValueError):
        perfil_id = 0

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    idade = _calcular_idade(perfil.data_nascimento)

    try:
        limite = int(request.GET.get("limite", 6))
    except (TypeError, ValueError):
        limite = 6
    limite = min(18, max(1, limite))

    skills_ativas = list(
        Skill.objects.filter(ativa=True).order_by("ordem", "nome")
    )
    diagnostico = _diagnostico_skills_crianca(
        perfil,
        skills_ativas=skills_ativas,
    )
    slugs_enfase = _slugs_enfase_solicitados(request, skills_ativas)

    if slugs_enfase:
        slugs_alvo = slugs_enfase
    else:
        slugs_alvo = [
            item["slug"]
            for item in diagnostico.get("recomendadas", [])
        ]

    slugs_repetidas = {
        item["slug"]
        for item in diagnostico.get("repetidas", [])
    }

    sugestoes_qs = (
        SugestaoTarefa.objects
        .filter(ativa=True)
        .prefetch_related("skills_associadas__skill")
    )

    if idade is not None:
        sugestoes_qs = sugestoes_qs.filter(
            idade_minima__lte=idade,
            idade_maxima__gte=idade,
        )
    else:
        sugestoes_qs = sugestoes_qs.filter(
            idade_minima__lte=8,
            idade_maxima__gte=8,
        )

    titulos_existentes = set(
        MoldeTarefa.objects
        .filter(crianca=perfil, ativa=True)
        .values_list("titulo", flat=True)
    )

    candidatas = [
        sugestao
        for sugestao in sugestoes_qs
        if sugestao.titulo not in titulos_existentes
    ]

    candidatas.sort(
        key=lambda sugestao: (
            -_pontuar_sugestao_por_skills(
                sugestao,
                slugs_alvo,
                slugs_repetidas,
            ),
            sugestao.ordem,
            sugestao.titulo,
        )
    )

    dados = []
    for sugestao in candidatas[:limite]:
        item = _serializar_sugestao(sugestao)
        slugs_item = {skill["slug"] for skill in item["skills"]}
        item["skills_enfase"] = [
            slug for slug in slugs_alvo if slug in slugs_item
        ]
        dados.append(item)

    if idade is None:
        subtitulo = (
            "A data de nascimento não foi informada. Exibindo sugestões gerais."
        )
    elif slugs_enfase:
        nomes = [
            skill.nome for skill in skills_ativas if skill.slug in slugs_enfase
        ]
        subtitulo = "Priorizando " + ", ".join(nomes) + "."
    else:
        subtitulo = diagnostico.get("resumo", "")

    return JsonResponse(
        {
            "crianca": perfil.nome_exibicao,
            "idade": idade,
            "subtitulo": subtitulo,
            "modo_enfase": "manual" if slugs_enfase else "automatico",
            "skills_enfase": slugs_enfase,
            "diagnostico": diagnostico,
            "sugestoes": dados,
        }
    )


@login_required(login_url="login")
@require_POST
def rotina_alternar(
    request,
    molde_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    molde = get_object_or_404(
        MoldeTarefa,
        id=molde_id,
        familia=familia,
    )

    molde.ativa = not molde.ativa
    molde.save(
        update_fields=[
            "ativa",
            "atualizado_em",
        ]
    )

    estado = (
        "ativada"
        if molde.ativa
        else "desativada"
    )

    messages.success(
        request,
        f"Rotina {estado}.",
    )

    return redirect(
        "rotinas_listar"
    )


@login_required(login_url="login")
@require_POST
def rotina_excluir(
    request,
    molde_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    molde = get_object_or_404(
        MoldeTarefa,
        id=molde_id,
        familia=familia,
    )

    titulo = molde.titulo
    molde.delete()

    messages.success(
        request,
        (
            f'Rotina "{titulo}" excluída. '
            "As tarefas históricas foram preservadas."
        ),
    )

    return redirect(
        "rotinas_listar"
    )


@login_required(login_url="login")
def tarefa_bonus_criar(
    request,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    if request.method == "POST":
        form = TarefaBonusForm(
            request.POST,
            familia=familia,
        )

        if form.is_valid():
            dados = form.cleaned_data

            tarefa = InstanciaTarefa.objects.create(
                familia=familia,
                crianca=dados["crianca"],
                criada_por=request.user,
                origem=InstanciaTarefa.Origem.BONUS,
                titulo=dados["titulo"],
                descricao=dados["descricao"],
                pontos_base=dados["pontos_base"],
                data_referencia=timezone.localdate(),
            )

            salvar_skills_tarefa_bonus(
                tarefa,
                form.obter_impactos_skills(),
            )

            messages.success(
                request,
                "Tarefa bônus lançada!",
            )

            return redirect(
                "inicio"
            )
    else:
        form = TarefaBonusForm(
            familia=familia
        )

    return render(
        request,
        "tarefas/bonus/form.html",
        {
            "form": form,
            "skills_disponiveis": (
                _skills_para_formulario(
                    request
                )
            ),
        },
    )


@login_required(login_url="login")
def minhas_tarefas(request):
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
                "Seu usuário não possui um "
                "perfil infantil vinculado."
            ),
        )
        return redirect("inicio")

    hoje = timezone.localdate()

    processar_rotinas(
        familia=perfil.familia,
        data=hoje,
    )

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            crianca=perfil,
            data_referencia=hoje,
        )
        .prefetch_related(
            "skills_snapshot"
        )
        .order_by(
            "status",
            "criada_em",
        )
    )

    return render(
        request,
        "tarefas/minhas_tarefas.html",
        {
            "perfil": perfil,
            "tarefas": tarefas,
            "hoje": hoje,
        },
    )


@login_required(login_url="login")
def tarefas_crianca_tutor(
    request,
    perfil_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    hoje = timezone.localdate()

    processar_rotinas(
        familia=familia,
        data=hoje,
    )

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            crianca=perfil,
            data_referencia=hoje,
        )
        .prefetch_related(
            "skills_snapshot"
        )
        .order_by(
            "status",
            "criada_em",
        )
    )

    return render(
        request,
        "tarefas/tarefas_crianca_tutor.html",
        {
            "perfil": perfil,
            "tarefas": tarefas,
            "hoje": hoje,
        },
    )


@login_required(login_url="login")
def historico_crianca_tutor(
    request,
    perfil_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    perfil = get_object_or_404(
        PerfilCrianca,
        id=perfil_id,
        familia=familia,
    )

    return _render_historico(
        request,
        perfil,
    )


@login_required(login_url="login")
def meu_historico(
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

    return _render_historico(
        request,
        perfil,
    )


@login_required(login_url="login")
@require_GET
def foto_tarefa_privada(request, tarefa_id):
    if request.user.tipo == Usuario.Tipo.TUTOR:
        familia = _familia_do_tutor(request)
        tarefa = get_object_or_404(
            InstanciaTarefa.objects.select_related("crianca"),
            id=tarefa_id,
            familia=familia,
        )
    elif request.user.tipo == Usuario.Tipo.CRIANCA:
        perfil = getattr(
            request.user,
            "perfil_crianca",
            None,
        )

        tarefa = get_object_or_404(
            InstanciaTarefa.objects.select_related("crianca"),
            id=tarefa_id,
            crianca=perfil,
        )
    else:
        tarefa = None

    if not tarefa or not tarefa.foto:

        from django.http import Http404
        raise Http404

    arquivo = tarefa.foto.storage.open(
        tarefa.foto.name,
        "rb",
    )
    content_type = (
        mimetypes.guess_type(tarefa.foto.name)[0]
        or "application/octet-stream"
    )

    resposta = FileResponse(
        arquivo,
        content_type=content_type,
    )
    resposta["Content-Disposition"] = (
        'inline; filename="evidencia-tarefa.jpg"'
    )
    resposta["Cache-Control"] = (
        "private, no-store, no-cache, must-revalidate, max-age=0"
    )
    resposta["Pragma"] = "no-cache"
    resposta["X-Content-Type-Options"] = "nosniff"

    return resposta


@login_required(login_url="login")
def enviar_foto(
    request,
    tarefa_id,
):
    tarefa = get_object_or_404(
        InstanciaTarefa.objects
        .select_related(
            "crianca",
            "familia",
        ),
        id=tarefa_id,
    )

    if not _pode_operar_tarefa(
        request,
        tarefa,
    ):
        messages.error(
            request,
            "Você não possui acesso a esta tarefa.",
        )
        return redirect("inicio")

    if not tarefa.pode_enviar_comprovante:
        messages.warning(
            request,
            "Esta tarefa não está disponível para envio.",
        )
        return redirect("inicio")

    if request.method == "POST":
        form = EnvioComprovanteForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            enviar_comprovante(
                tarefa,
                form.cleaned_data["foto"],
            )

            messages.success(
                request,
                (
                    "Foto enviada! Agora a tarefa "
                    "está aguardando revisão."
                ),
            )

            if request.user.tipo == Usuario.Tipo.CRIANCA:
                return redirect(
                    "minhas_tarefas"
                )

            return redirect(
                "tarefas_crianca_tutor",
                perfil_id=tarefa.crianca_id,
            )
    else:
        form = EnvioComprovanteForm()

    return render(
        request,
        "tarefas/enviar_foto.html",
        {
            "form": form,
            "tarefa": tarefa,
        },
    )


@login_required(login_url="login")
def revisoes_listar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    processar_rotinas(
        familia=familia
    )

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            familia=familia,
            status=InstanciaTarefa.Status.REVISAO,
        )
        .select_related("crianca")
        .prefetch_related(
            "skills_snapshot"
        )
        .order_by("enviada_em")
    )

    return render(
        request,
        "tarefas/revisoes/lista.html",
        {
            "tarefas": tarefas,
        },
    )


@login_required(login_url="login")
def revisao_detalhe(
    request,
    tarefa_id,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = _familia_do_tutor(
        request
    )

    tarefa = get_object_or_404(
        InstanciaTarefa.objects
        .select_related("crianca")
        .prefetch_related(
            "skills_snapshot"
        ),
        id=tarefa_id,
        familia=familia,
        status=InstanciaTarefa.Status.REVISAO,
    )

    if request.method == "POST":
        form = RevisaoTarefaForm(
            request.POST
        )

        if form.is_valid():
            acao = request.POST.get(
                "acao"
            )

            feedback = (
                form.cleaned_data.get(
                    "feedback_tutor"
                )
                or ""
            )

            if acao == "aprovar":
                pontos = (
                    form.cleaned_data.get(
                        "pontos_concedidos"
                    )
                )

                if pontos is None:
                    pontos = tarefa.pontos_base

                try:
                    resultado = aprovar_tarefa(
                        tarefa=tarefa,
                        tutor=request.user,
                        pontos=pontos,
                        feedback=feedback,
                    )
                except ValueError as erro:
                    messages.error(
                        request,
                        str(erro),
                    )
                else:
                    if resultado["evoluiu"]:
                        movimento = resultado["movimento"]
                        messages.success(
                            request,
                            (
                                f"🎉 {tarefa.crianca.nome_exibicao} "
                                "evoluiu para o nível "
                                f"{movimento.nivel_depois}!"
                            ),
                        )
                    else:
                        messages.success(
                            request,
                            (
                                "Tarefa aprovada e "
                                f"{pontos} pontos concedidos!"
                            ),
                        )

                    evolucoes = resultado[
                        "evolucoes_skills"
                    ]

                    if evolucoes:
                        resumo = ", ".join(
                            (
                                f"{item['skill'].icone} "
                                f"{item['skill'].nome} "
                                f"→ nível "
                                f"{item['nivel_depois']}"
                            )
                            for item in evolucoes
                        )
                        messages.info(
                            request,
                            (
                                "Habilidade(s) evoluída(s): "
                                f"{resumo}."
                            ),
                        )

                    return redirect(
                        "revisoes_listar"
                    )

            elif acao == "rejeitar":
                try:
                    rejeitar_tarefa(
                        tarefa=tarefa,
                        tutor=request.user,
                        feedback=feedback,
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
                            "Tarefa rejeitada. "
                            "Ela poderá ser enviada novamente."
                        ),
                    )
                    return redirect(
                        "revisoes_listar"
                    )
            else:
                messages.error(
                    request,
                    "Escolha aprovar ou rejeitar.",
                )
    else:
        form = RevisaoTarefaForm(
            pontos_iniciais=tarefa.pontos_base
        )

    return render(
        request,
        "tarefas/revisoes/detalhe.html",
        {
            "tarefa": tarefa,
            "form": form,
        },
    )
