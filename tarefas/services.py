from contextlib import suppress
from datetime import timedelta
import json
import logging
import os
import re

from dotenv import load_dotenv
from django.db import transaction
from django.utils import timezone

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None


load_dotenv()
logger = logging.getLogger(__name__)


class ErroSugestaoIA(RuntimeError):
    """Erro controlado ao gerar sugestões com o provedor de IA."""


class ConfiguracaoIAAusente(ErroSugestaoIA):
    """A chave de acesso ao Gemini não foi configurada."""


class DependenciaIAAusente(ErroSugestaoIA):
    """O SDK atual do Gemini não está instalado no ambiente."""


def _extrair_json_ia(texto):
    """Extrai o JSON mesmo se o provedor devolver cercas de markdown."""
    conteudo = (texto or "").strip()

    if conteudo.startswith("```"):
        conteudo = re.sub(r"^```(?:json)?\s*", "", conteudo, flags=re.I)
        conteudo = re.sub(r"\s*```$", "", conteudo)

    try:
        return json.loads(conteudo)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ErroSugestaoIA(
            "A IA respondeu em um formato que não pôde ser interpretado."
        ) from exc


def _normalizar_sugestoes_ia(dados, skills_validas):
    """Valida e reduz a resposta da IA ao formato usado pela interface."""
    if isinstance(dados, dict):
        dados = dados.get("sugestoes", [])

    if not isinstance(dados, list):
        return []

    slugs_validos = {
        str(item.get("slug", "")).strip(): item
        for item in (skills_validas or [])
        if str(item.get("slug", "")).strip()
    }

    sugestoes = []

    for item in dados:
        if not isinstance(item, dict):
            continue

        titulo = str(item.get("titulo", "")).strip()[:120]
        if not titulo:
            continue

        descricao = str(item.get("descricao", "")).strip()[:280]
        icone = str(item.get("icone", "✨") or "✨").strip()[:8] or "✨"

        try:
            pontos = int(item.get("pontos", 10) or 10)
        except (TypeError, ValueError):
            pontos = 10

        pontos = min(30, max(5, pontos))

        skills = []
        vistos = set()

        for skill in item.get("skills", []) or []:
            if not isinstance(skill, dict):
                continue

            slug = str(skill.get("slug", "")).strip()
            if slug not in slugs_validos or slug in vistos:
                continue

            try:
                impacto = int(skill.get("impacto", 0) or 0)
            except (TypeError, ValueError):
                impacto = 0

            if impacto not in {1, 2, 3}:
                continue

            skills.append({
                "slug": slug,
                "impacto": impacto,
            })
            vistos.add(slug)

            if len(skills) >= 3:
                break

        if not skills:
            continue

        sugestoes.append({
            "icone": icone,
            "titulo": titulo,
            "descricao": descricao,
            "pontos": pontos,
            "skills": skills,
        })

        if len(sugestoes) >= 6:
            break

    return sugestoes


def gerar_sugestao_rotina(
    idade_crianca,
    contexto="rotina diária",
    skills_validas=None,
    diagnostico_skills=None,
    skills_enfase=None,
    titulos_existentes=None,
):
    """Gera tarefas com Skills, usando evolução e cobertura atuais como contexto."""
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    if not api_key:
        raise ConfiguracaoIAAusente(
            "A IA ainda não está configurada. Defina GEMINI_API_KEY no arquivo .env."
        )

    if genai is None or genai_types is None:
        raise DependenciaIAAusente(
            "O pacote google-genai não está instalado. Execute: pip install -r requirements.txt"
        )

    modelo = (
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        or "gemini-3.5-flash-lite"
    )

    skills_validas = list(skills_validas or [])
    skills_enfase = list(skills_enfase or [])[:3]
    diagnostico_skills = diagnostico_skills or {}
    titulos_existentes = [
        str(titulo).strip()
        for titulo in (titulos_existentes or [])
        if str(titulo).strip()
    ][:30]

    catalogo_skills = "\n".join(
        f'- {item["slug"]}: {item["nome"]} — {item.get("descricao", "")}'
        for item in skills_validas
    )

    linhas_diagnostico = []
    for item in diagnostico_skills.get("skills", []):
        linhas_diagnostico.append(
            "- {slug}: XP={xp}, nível={nivel}, rotinas_ativas={rotinas}, "
            "carga_planejada={carga}, prioridade={prioridade}/100{repetida}".format(
                slug=item.get("slug", ""),
                xp=item.get("xp", 0),
                nivel=item.get("nivel", 1),
                rotinas=item.get("rotinas_ativas", 0),
                carga=item.get("carga", 0),
                prioridade=item.get("prioridade", 0),
                repetida=" (muito repetida)" if item.get("repetida") else "",
            )
        )

    recomendadas = [
        item.get("slug")
        for item in diagnostico_skills.get("recomendadas", [])
        if item.get("slug")
    ]
    repetidas = [
        item.get("slug")
        for item in diagnostico_skills.get("repetidas", [])
        if item.get("slug")
    ]

    if skills_enfase:
        orientacao_enfase = (
            "A família escolheu manualmente dar ênfase às Skills: "
            + ", ".join(skills_enfase)
            + ". A escolha manual da família tem prioridade sobre o equilíbrio automático. "
              "Pelo menos 4 das 6 opções devem praticar diretamente uma dessas Skills, "
              "mas só associe a Skill quando houver relação real com a tarefa. As outras "
              "opções podem ajudar a equilibrar lacunas importantes."
        )
    else:
        orientacao_enfase = (
            "A família deixou o modo de equilíbrio automático. Priorize Skills pouco "
            "desenvolvidas e pouco presentes nas rotinas. As prioridades detectadas são: "
            + (", ".join(recomendadas) if recomendadas else "nenhuma específica")
            + ". Evite reforçar sem necessidade as Skills já muito repetidas: "
            + (", ".join(repetidas) if repetidas else "nenhuma")
            + "."
        )

    tarefas_existentes = (
        "\n".join(f"- {titulo}" for titulo in titulos_existentes)
        or "- Nenhuma tarefa ativa informada"
    )
    diagnostico_texto = "\n".join(linhas_diagnostico) or "- Sem histórico suficiente"

    prompt = f"""
Atue como especialista em rotinas infantis e gamificação educativa.
Crie 6 opções de tarefas seguras, simples, concretas e adequadas para uma criança de
{idade_crianca} anos, considerando o contexto: {contexto}.

O objetivo NÃO é apenas criar tarefas variadas: use também a evolução das habilidades
já registrada e a distribuição das Skills nas rotinas ativas para evitar concentração
excessiva em uma habilidade e ajudar a desenvolver as menos trabalhadas.

{orientacao_enfase}

Diagnóstico atual das Skills (dados agregados, sem nome da criança):
{diagnostico_texto}

Tarefas ativas já existentes — evite sugerir a mesma tarefa ou uma variação quase idêntica:
{tarefas_existentes}

Skills disponíveis. Use SOMENTE estes slugs:
{catalogo_skills}

Para cada tarefa:
- escolha um único emoji realmente representativo em "icone";
- associe de 1 a 3 Skills que a tarefa realmente pratica;
- impacto 1 = relação leve/secundária;
- impacto 2 = relação clara/importante;
- impacto 3 = habilidade central diretamente praticada;
- não marque Skills apenas para cumprir a ênfase;
- não concentre todas as opções na mesma combinação de Skills;
- escolha pontos entre 5 e 30, proporcionais ao esforço e à idade;
- descrição curta e objetiva;
- evite fogo, medicamentos, produtos químicos, ferramentas perigosas,
  atividades incompatíveis com a idade ou exposição de dados pessoais;
- não use o nome da criança;
- não invente Skills fora do catálogo.

Retorne EXCLUSIVAMENTE um array JSON válido neste formato:
[
  {{
    "icone": "🛏️",
    "titulo": "Arrumar a cama",
    "descricao": "Organizar a cama ao levantar.",
    "pontos": 10,
    "skills": [
      {{"slug": "autonomia", "impacto": 3}},
      {{"slug": "organizacao", "impacto": 2}}
    ]
  }}
]
""".strip()

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=modelo,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.55,
            ),
        )
    except Exception as exc:
        logger.exception(
            "Falha ao consultar o Gemini com o modelo %s",
            modelo,
        )
        raise ErroSugestaoIA(
            "Não foi possível gerar sugestões com a IA neste momento."
        ) from exc
    finally:
        with suppress(Exception):
            client.close()

    dados = _extrair_json_ia(getattr(response, "text", ""))
    sugestoes = _normalizar_sugestoes_ia(dados, skills_validas)

    if not sugestoes:
        raise ErroSugestaoIA(
            "A IA respondeu, mas não retornou tarefas com Skills válidas."
        )

    return sugestoes


from gamificacao.services import (
    avaliar_conquistas,
    copiar_skills_molde_para_tarefa,
    criar_alertas_tarefa_nao_realizada,
    gerar_resumos_familia,
    registrar_penalidade_tarefa_nao_realizada,
    registrar_pontos_aprovacao,
    registrar_xp_skills_aprovacao,
)

from .models import InstanciaTarefa, MoldeTarefa


def gerar_tarefas_do_dia(
    familia=None,
    data=None,
):
    data = data or timezone.localdate()

    moldes = (
        MoldeTarefa.objects
        .filter(ativa=True)
        .select_related(
            "familia",
            "crianca",
        )
    )

    if familia is not None:
        moldes = moldes.filter(
            familia=familia
        )

    criadas = 0

    for molde in moldes:
        if not molde.deve_gerar_em(data):
            continue

        tarefa, criada = (
            InstanciaTarefa.objects
            .get_or_create(
                molde=molde,
                data_referencia=data,
                defaults={
                    "familia": molde.familia,
                    "crianca": molde.crianca,
                    "criada_por": molde.criado_por,
                    "origem": InstanciaTarefa.Origem.MOLDE,
                    "titulo": molde.titulo,
                    "descricao": molde.descricao,
                    "pontos_base": molde.pontos_base,
                    "periodo": molde.periodo,
                    "horario": molde.horario,
                    "lembrete_ativo": molde.lembrete_ativo,
                },
            )
        )

        if criada:
            copiar_skills_molde_para_tarefa(
                molde,
                tarefa,
            )
            criadas += 1

    return criadas


def encerrar_tarefas_antigas(
    familia=None,
    hoje=None,
):
    hoje = hoje or timezone.localdate()

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            data_referencia__lt=hoje,
            status__in=[
                InstanciaTarefa.Status.PENDENTE,
                InstanciaTarefa.Status.REJEITADA,
            ],
        )
        .select_related(
            "familia",
            "crianca",
        )
    )

    if familia is not None:
        tarefas = tarefas.filter(
            familia=familia
        )

    quantidade = 0

    for tarefa in tarefas:
        tarefa.status = (
            InstanciaTarefa.Status.NAO_REALIZADA
        )
        tarefa.save(
            update_fields=[
                "status",
                "atualizada_em",
            ]
        )

        movimento = (
            registrar_penalidade_tarefa_nao_realizada(
                tarefa
            )
        )

        criar_alertas_tarefa_nao_realizada(
            tarefa,
            movimento=movimento,
        )

        quantidade += 1

    return quantidade


def processar_lembretes(
    familia=None,
    agora=None,
):
    from gamificacao.models import NotificacaoSistema
    from usuarios.models import Usuario

    agora = agora or timezone.localtime()
    hoje = agora.date()
    horario_atual = agora.time().replace(
        second=0,
        microsecond=0,
    )

    tarefas = (
        InstanciaTarefa.objects
        .filter(
            data_referencia=hoje,
            lembrete_ativo=True,
            status__in=[
                InstanciaTarefa
                .Status
                .PENDENTE,
                InstanciaTarefa
                .Status
                .REJEITADA,
            ],
        )
        .select_related(
            "crianca",
            "crianca__usuario",
            "familia",
        )
    )

    if familia is not None:
        tarefas = tarefas.filter(
            familia=familia
        )

    criadas = 0

    for tarefa in tarefas:
        horario = tarefa.horario_lembrete

        if horario is None:
            continue

        if horario_atual < horario:
            continue

        destinos = []

        if (
            tarefa.crianca.usuario_id
            and tarefa.crianca.acesso_proprio
            and tarefa.crianca.usuario.is_active
        ):
            destinos.append(
                tarefa.crianca.usuario
            )
        else:
            destinos.extend(
                tarefa.familia.tutores.all()
            )

        for usuario in destinos:
            _, criada = (
                NotificacaoSistema.objects
                .get_or_create(
                    usuario_destino=usuario,
                    chave=(
                        f"lembrete:"
                        f"{tarefa.id}:"
                        f"{usuario.id}"
                    ),
                    defaults={
                        "crianca": tarefa.crianca,
                        "tarefa": tarefa,
                        "tipo": (
                            NotificacaoSistema
                            .Tipo
                            .LEMBRETE_TAREFA
                        ),
                        "titulo": (
                            f"⏰ Hora de "
                            f"{tarefa.titulo}"
                        ),
                        "mensagem": (
                            f"Esta tarefa vale "
                            f"{tarefa.pontos_base} ponto(s)."
                        ),
                        "url_destino": (
                            "/minhas-tarefas/"
                            if (
                                usuario.tipo
                                == Usuario.Tipo.CRIANCA
                            )
                            else (
                                f"/criancas/"
                                f"{tarefa.crianca_id}/"
                                f"tarefas/"
                            )
                        ),
                    },
                )
            )

            if criada:
                criadas += 1

    return criadas

def processar_rotinas(
    familia=None,
    data=None,
):
    from usuarios.models import Familia

    data = data or timezone.localdate()

    encerradas = encerrar_tarefas_antigas(
        familia=familia,
        hoje=data,
    )

    criadas = gerar_tarefas_do_dia(
        familia=familia,
        data=data,
    )

    if familia is not None:
        gerar_resumos_familia(
            familia=familia,
            hoje=data,
        )
    else:
        for familia_item in Familia.objects.all():
            gerar_resumos_familia(
                familia=familia_item,
                hoje=data,
            )

    lembretes = processar_lembretes(
        familia=familia
    )

    return {
        "criadas": criadas,
        "encerradas": encerradas,
        "lembretes": lembretes,
    }


def calcular_indicadores_periodo(
    *,
    perfil=None,
    familia=None,
    dias=7,
):
    hoje = timezone.localdate()
    inicio = hoje - timedelta(
        days=dias - 1
    )

    tarefas = InstanciaTarefa.objects.filter(
        data_referencia__gte=inicio,
        data_referencia__lte=hoje,
    )

    if perfil is not None:
        tarefas = tarefas.filter(
            crianca=perfil
        )

    if familia is not None:
        tarefas = tarefas.filter(
            familia=familia
        )

    aprovadas = tarefas.filter(
        status=InstanciaTarefa.Status.APROVADA
    ).count()

    nao_realizadas = tarefas.filter(
        status=InstanciaTarefa.Status.NAO_REALIZADA
    ).count()

    pendentes = tarefas.filter(
        status=InstanciaTarefa.Status.PENDENTE
    ).count()

    revisao = tarefas.filter(
        status=InstanciaTarefa.Status.REVISAO
    ).count()

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

    tarefas_com_envio = tarefas.exclude(
        enviada_em__isnull=True
    )

    atrasadas = sum(
        1
        for tarefa in tarefas_com_envio
        if tarefa.procrastinou
    )

    return {
        "dias": dias,
        "inicio": inicio,
        "fim": hoje,
        "total": tarefas.count(),
        "aprovadas": aprovadas,
        "nao_realizadas": nao_realizadas,
        "pendentes": pendentes,
        "revisao": revisao,
        "finalizadas": finalizadas,
        "taxa_conclusao": taxa_conclusao,
        "atrasadas": atrasadas,
    }


def enviar_comprovante(
    tarefa,
    foto,
):
    if not tarefa.pode_enviar_comprovante:
        raise ValueError(
            "Esta tarefa não aceita um novo comprovante."
        )

    tarefa.foto = foto
    tarefa.enviada_em = timezone.now()
    tarefa.status = InstanciaTarefa.Status.REVISAO
    tarefa.feedback_tutor = ""
    tarefa.pontos_concedidos = None
    tarefa.revisada_por = None
    tarefa.revisada_em = None

    tarefa.save(
        update_fields=[
            "foto",
            "enviada_em",
            "status",
            "feedback_tutor",
            "pontos_concedidos",
            "revisada_por",
            "revisada_em",
            "atualizada_em",
        ]
    )

    return tarefa


@transaction.atomic
def aprovar_tarefa(
    tarefa,
    tutor,
    pontos,
    feedback="",
):
    tarefa = (
        InstanciaTarefa.objects
        .select_for_update()
        .get(pk=tarefa.pk)
    )

    if tarefa.status != InstanciaTarefa.Status.REVISAO:
        raise ValueError(
            "A tarefa não está aguardando revisão."
        )

    pontos = max(0, int(pontos))

    movimento = registrar_pontos_aprovacao(
        tarefa=tarefa,
        tutor=tutor,
        pontos=pontos,
    )

    evolucoes_skills = (
        registrar_xp_skills_aprovacao(
            tarefa
        )
    )

    tarefa.status = InstanciaTarefa.Status.APROVADA
    tarefa.feedback_tutor = feedback or ""
    tarefa.pontos_concedidos = pontos
    tarefa.revisada_por = tutor
    tarefa.revisada_em = timezone.now()

    tarefa.save(
        update_fields=[
            "status",
            "feedback_tutor",
            "pontos_concedidos",
            "revisada_por",
            "revisada_em",
            "atualizada_em",
        ]
    )

    avaliar_conquistas(
        tarefa.crianca
    )

    return {
        "tarefa": tarefa,
        "movimento": movimento,
        "evoluiu": (
            movimento.nivel_depois
            > movimento.nivel_antes
        ),
        "evolucoes_skills": evolucoes_skills,
    }


@transaction.atomic
def rejeitar_tarefa(
    tarefa,
    tutor,
    feedback="",
):
    tarefa = (
        InstanciaTarefa.objects
        .select_for_update()
        .get(pk=tarefa.pk)
    )

    if tarefa.status != InstanciaTarefa.Status.REVISAO:
        raise ValueError(
            "A tarefa não está aguardando revisão."
        )

    tarefa.status = InstanciaTarefa.Status.REJEITADA
    tarefa.feedback_tutor = feedback or ""
    tarefa.pontos_concedidos = 0
    tarefa.revisada_por = tutor
    tarefa.revisada_em = timezone.now()

    tarefa.save(
        update_fields=[
            "status",
            "feedback_tutor",
            "pontos_concedidos",
            "revisada_por",
            "revisada_em",
            "atualizada_em",
        ]
    )

    return tarefa
