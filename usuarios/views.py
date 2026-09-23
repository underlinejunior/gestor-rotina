from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from gamificacao.models import NotificacaoSistema

from .forms import CadastroTutorForm, CodigoConviteTutorForm, CriancaForm
from .models import ConviteTutor, Familia, PerfilCrianca, Usuario


def obter_familia_tutor(usuario):
    familia = usuario.familias_como_tutor.first()

    if familia is None:
        nome = usuario.first_name or usuario.username

        familia = Familia.objects.create(
            nome=f"Família de {nome}"
        )
        familia.tutores.add(usuario)

    return familia


def obter_celebracao_usuario(
    usuario,
    tipos=None,
):
    if not usuario.is_authenticated:
        return None

    if not usuario.boas_vindas_exibidas:
        usuario.boas_vindas_exibidas = True
        usuario.save(
            update_fields=["boas_vindas_exibidas"]
        )

        perfil = getattr(
            usuario,
            "perfil_crianca",
            None,
        )

        if usuario.tipo == Usuario.Tipo.CRIANCA:
            nome = (
                perfil.nome_exibicao
                if perfil
                else (usuario.first_name or usuario.username)
            )
            avatar = (
                perfil.avatar_emoji
                if perfil
                else "🎉"
            )
        else:
            nome = usuario.first_name or usuario.username
            avatar = "🎉"

        return {
            "tipo": "PRIMEIRO_ACESSO",
            "titulo": f"Bem-vindo, {nome}!",
            "mensagem": (
                "Seu espaço já está pronto para acompanhar rotinas, "
                "recompensas e conquistas com muito mais diversão."
            ),
            "avatar_emoji": avatar,
            "crianca_nome": nome,
            "nivel_anterior": None,
            "nivel_novo": None,
            "titulo_novo_nivel": "",
            "pill_text": "✨ Primeiro acesso",
            "highlight_text": (
                "Prepare-se para completar tarefas, ganhar estrelas "
                "e viver uma rotina muito mais divertida."
            ),
        }

    if tipos is None:
        tipos = [
            NotificacaoSistema.Tipo.RECOMPENSA,
            NotificacaoSistema.Tipo.CONQUISTA,
            NotificacaoSistema.Tipo.NIVEL_AVATAR,
        ]

    notificacao = (
        NotificacaoSistema.objects
        .filter(
            usuario_destino=usuario,
            visualizada=False,
            tipo__in=tipos,
        )
        .select_related("crianca")
        .order_by("-criada_em")
        .first()
    )

    if notificacao:
        evento = notificacao.to_evento()
        notificacao.visualizada = True
        notificacao.save(
            update_fields=["visualizada"]
        )
        return evento

    return None


def login_view(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    erro = None

    if request.method == "POST":
        username = (
            request.POST.get("username") or ""
        ).strip()

        password = (
            request.POST.get("password") or ""
        )

        usuario = authenticate(
            request,
            username=username,
            password=password,
        )

        if usuario is not None:
            login(request, usuario)

            if (
                usuario.tipo == Usuario.Tipo.TUTOR
                and usuario.privacidade_pendente
            ):
                return redirect("privacidade_aceite")

            return redirect("inicio")

        erro = "Usuário ou senha inválidos."

    return render(
        request,
        "usuarios/login.html",
        {
            "erro": erro,
            "google_login_disponivel": getattr(
                settings,
                "GOOGLE_OAUTH_ENABLED",
                False,
            ),
        },
    )


def cadastro_tutor_view(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        form = CadastroTutorForm(
            request.POST
        )

        if form.is_valid():
            usuario = form.save()

            familia = Familia.objects.create(
                nome=(
                    "Família de "
                    f"{usuario.first_name or usuario.username}"
                )
            )

            familia.tutores.add(usuario)

            usuario.privacidade_aceita_em = timezone.now()
            usuario.privacidade_versao = getattr(
                settings,
                "PRIVACY_POLICY_VERSION",
                "",
            )
            usuario.save(
                update_fields=[
                    "privacidade_aceita_em",
                    "privacidade_versao",
                ]
            )

            login(
                request,
                usuario,
                backend="django.contrib.auth.backends.ModelBackend",
            )

            messages.success(
                request,
                "Conta criada com sucesso!",
            )

            return redirect("inicio")
    else:
        form = CadastroTutorForm()

    return render(
        request,
        "usuarios/cadastro.html",
        {"form": form},
    )


def privacidade_politica(request):
    return render(
        request,
        "usuarios/privacidade/politica.html",
        {
            "versao": getattr(
                settings,
                "PRIVACY_POLICY_VERSION",
                "",
            ),
            "retencao_dias": getattr(
                settings,
                "EVIDENCE_RETENTION_DAYS",
                180,
            ),
            "contato_privacidade": getattr(
                settings,
                "PRIVACY_CONTACT_EMAIL",
                "",
            ),
        },
    )


@login_required(login_url="login")
def privacidade_aceite(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    versao = getattr(
        settings,
        "PRIVACY_POLICY_VERSION",
        "",
    )

    if not request.user.privacidade_pendente:
        return redirect("inicio")

    if request.method == "POST":
        if request.POST.get("aceite") != "on":
            messages.error(
                request,
                "É necessário confirmar a ciência da Política de Privacidade.",
            )
        else:
            request.user.privacidade_aceita_em = timezone.now()
            request.user.privacidade_versao = versao
            request.user.save(
                update_fields=[
                    "privacidade_aceita_em",
                    "privacidade_versao",
                ]
            )

            messages.success(
                request,
                "Preferências de privacidade registradas.",
            )
            return redirect("inicio")

    return render(
        request,
        "usuarios/privacidade/aceite.html",
        {
            "versao": versao,
        },
    )


@login_required(login_url="login")
def privacidade_central(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(request.user)

    return render(
        request,
        "usuarios/privacidade/central.html",
        {
            "familia": familia,
            "versao": getattr(
                settings,
                "PRIVACY_POLICY_VERSION",
                "",
            ),
            "retencao_dias": getattr(
                settings,
                "EVIDENCE_RETENTION_DAYS",
                180,
            ),
        },
    )


@login_required(login_url="login")
def privacidade_exportar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    from tarefas.models import InstanciaTarefa, MoldeTarefa
    from gamificacao.models import (
        ConquistaCrianca,
        MovimentoPontos,
        MovimentoSkill,
        ProgressoSkill,
        ResgateRecompensa,
    )

    familia = obter_familia_tutor(request.user)

    criancas = list(
        familia.criancas
        .select_related("usuario")
        .order_by("id")
    )
    crianca_ids = [item.id for item in criancas]

    dados = {
        "exportado_em": timezone.now(),
        "politica_privacidade_versao": getattr(
            settings,
            "PRIVACY_POLICY_VERSION",
            "",
        ),
        "familia": {
            "id": familia.id,
            "nome": familia.nome,
            "criada_em": familia.criada_em,
        },
        "tutores": list(
            familia.tutores.values(
                "id",
                "username",
                "first_name",
                "last_name",
                "email",
            )
        ),
        "criancas": [
            {
                "id": item.id,
                "nome": item.nome_exibicao,
                "data_nascimento": item.data_nascimento,
                "avatar_tipo": item.avatar_tipo,
                "acesso_proprio": item.acesso_proprio,
                "usuario_acesso": (
                    item.usuario.username
                    if item.usuario_id
                    else None
                ),
                "saldo_pontos": item.saldo_pontos,
                "pontos_experiencia": item.pontos_experiencia,
                "criado_em": item.criado_em,
            }
            for item in criancas
        ],
        "moldes_tarefas": list(
            MoldeTarefa.objects
            .filter(familia=familia)
            .values(
                "id",
                "crianca_id",
                "titulo",
                "descricao",
                "pontos_base",
                "frequencia",
                "dias_semana",
                "periodo",
                "horario",
                "lembrete_ativo",
                "ativa",
                "criado_em",
                "atualizado_em",
            )
        ),
        "tarefas": list(
            InstanciaTarefa.objects
            .filter(familia=familia)
            .values(
                "id",
                "crianca_id",
                "titulo",
                "descricao",
                "pontos_base",
                "data_referencia",
                "status",
                "enviada_em",
                "feedback_tutor",
                "pontos_concedidos",
                "revisada_em",
                "criada_em",
            )
        ),
        "progresso_skills": list(
            ProgressoSkill.objects
            .filter(crianca_id__in=crianca_ids)
            .values(
                "crianca_id",
                "skill__slug",
                "skill__nome",
                "xp_total",
            )
        ),
        "movimentos_skills": list(
            MovimentoSkill.objects
            .filter(crianca_id__in=crianca_ids)
            .values(
                "crianca_id",
                "skill__slug",
                "xp",
                "criado_em",
            )
        ),
        "movimentos_pontos": list(
            MovimentoPontos.objects
            .filter(crianca_id__in=crianca_ids)
            .values(
                "crianca_id",
                "tipo",
                "pontos",
                "saldo_apos",
                "criado_em",
            )
        ),
        "resgates": list(
            ResgateRecompensa.objects
            .filter(crianca_id__in=crianca_ids)
            .values(
                "crianca_id",
                "titulo_snapshot",
                "custo_snapshot",
                "status",
                "solicitado_em",
                "concluido_em",
            )
        ),
        "conquistas": list(
            ConquistaCrianca.objects
            .filter(crianca_id__in=crianca_ids)
            .values(
                "crianca_id",
                "conquista__slug",
                "conquista__nome",
                "desbloqueada_em",
            )
        ),
    }

    resposta = JsonResponse(
        dados,
        encoder=DjangoJSONEncoder,
        json_dumps_params={
            "ensure_ascii": False,
            "indent": 2,
        },
    )
    resposta["Content-Disposition"] = (
        f'attachment; filename="dados-familia-{familia.id}.json"'
    )
    resposta["Cache-Control"] = "private, no-store"

    return resposta


@login_required(login_url="login")
@require_POST
def privacidade_apagar_evidencias(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    from tarefas.models import InstanciaTarefa

    familia = obter_familia_tutor(request.user)
    tarefas = (
        InstanciaTarefa.objects
        .filter(familia=familia)
        .exclude(foto="")
        .exclude(foto__isnull=True)
    )

    removidas = 0

    for tarefa in tarefas.iterator():
        if tarefa.foto:
            tarefa.foto.delete(save=False)
            tarefa.foto = None
            tarefa.save(
                update_fields=[
                    "foto",
                    "atualizada_em",
                ]
            )
            removidas += 1

    messages.success(
        request,
        f"{removidas} evidência(s) fotográfica(s) removida(s).",
    )
    return redirect("privacidade_central")


@login_required(login_url="login")
@require_POST
@transaction.atomic
def privacidade_excluir_conta(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    if request.POST.get("confirmacao", "").strip().upper() != "EXCLUIR":
        messages.error(
            request,
            "Digite EXCLUIR para confirmar a solicitação.",
        )
        return redirect("privacidade_central")

    from allauth.account.models import EmailAddress
    from allauth.socialaccount.models import SocialAccount
    from tarefas.models import InstanciaTarefa

    usuario = request.user
    familias = list(usuario.familias_como_tutor.all())
    familias_compartilhadas = False
    usuarios_crianca_para_excluir = set()

    for familia in familias:
        outros_tutores = familia.tutores.exclude(pk=usuario.pk)

        if outros_tutores.exists():
            familias_compartilhadas = True
            familia.tutores.remove(usuario)
            continue

        usuarios_crianca_para_excluir.update(
            familia.criancas
            .exclude(usuario__isnull=True)
            .values_list("usuario_id", flat=True)
        )

        for tarefa in (
            InstanciaTarefa.objects
            .filter(familia=familia)
            .exclude(foto="")
            .exclude(foto__isnull=True)
        ).iterator():
            if tarefa.foto:
                tarefa.foto.delete(save=False)

        familia.delete()

    EmailAddress.objects.filter(user=usuario).delete()
    SocialAccount.objects.filter(user=usuario).delete()

    logout(request)

    if familias_compartilhadas:
        # Registros históricos compartilhados podem possuir FK PROTECT para
        # quem criou uma rotina/recompensa. Nessa situação o usuário é
        # anonimizado e desativado, preservando a integridade do histórico.
        usuario.username = f"excluido_{usuario.pk}_{secrets.token_hex(4)}"
        usuario.first_name = ""
        usuario.last_name = ""
        usuario.email = ""
        usuario.is_active = False
        usuario.privacidade_aceita_em = None
        usuario.privacidade_versao = ""
        usuario.set_unusable_password()
        usuario.save()
    else:
        usuario.delete()

    if usuarios_crianca_para_excluir:
        Usuario.objects.filter(
            pk__in=usuarios_crianca_para_excluir,
            tipo=Usuario.Tipo.CRIANCA,
        ).delete()

    messages.success(
        request,
        "Solicitação de exclusão processada.",
    )
    return redirect("login")


@login_required(login_url="login")
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def inicio_view(request):
    from tarefas.models import InstanciaTarefa
    from tarefas.services import (
        calcular_indicadores_periodo,
        processar_rotinas,
    )

    hoje = timezone.localdate()
    celebracao_evento = obter_celebracao_usuario(
        request.user
    )

    if request.user.tipo == Usuario.Tipo.CRIANCA:
        perfil = getattr(
            request.user,
            "perfil_crianca",
            None,
        )

        if perfil:
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
                .order_by(
                    "status",
                    "criada_em",
                )
            )

            indicadores_semana = (
                calcular_indicadores_periodo(
                    perfil=perfil,
                    dias=7,
                )
            )

            from gamificacao.services import (
                calcular_sequencia,
            )

            sequencia_atual = (
                calcular_sequencia(
                    perfil
                )
            )

            conquistas_recentes = (
                perfil
                .conquistas_desbloqueadas
                .select_related(
                    "conquista"
                )
                .order_by(
                    "-desbloqueada_em"
                )[:3]
            )

            contexto = {
                "perfil": perfil,
                "tarefas": tarefas[:4],
                "total_pendentes": tarefas.filter(
                    status=(
                        InstanciaTarefa
                        .Status
                        .PENDENTE
                    )
                ).count(),
                "total_revisao": tarefas.filter(
                    status=(
                        InstanciaTarefa
                        .Status
                        .REVISAO
                    )
                ).count(),
                "total_concluidas": tarefas.filter(
                    status=(
                        InstanciaTarefa
                        .Status
                        .APROVADA
                    )
                ).count(),
                "indicadores_semana": (
                    indicadores_semana
                ),
                "sequencia_atual": (
                    sequencia_atual
                ),
                "conquistas_recentes": (
                    conquistas_recentes
                ),
                "celebracao_evento": (
                    celebracao_evento
                ),
            }

        else:
            contexto = {
                "perfil": None,
                "tarefas": [],
                "total_pendentes": 0,
                "total_revisao": 0,
                "total_concluidas": 0,
                "indicadores_semana": None,
                "celebracao_evento": (
                    celebracao_evento
                ),
            }

        return render(
            request,
            "usuarios/dashboard_crianca.html",
            contexto,
        )

    familia = obter_familia_tutor(
        request.user
    )

    processar_rotinas(
        familia=familia,
        data=hoje,
    )

    criancas = list(
        PerfilCrianca.objects
        .filter(familia=familia)
        .select_related("usuario")
        .order_by("nome")
    )

    from gamificacao.services import (
        calcular_sequencia,
    )

    for perfil in criancas:
        perfil.indicadores_semana = (
            calcular_indicadores_periodo(
                perfil=perfil,
                dias=7,
            )
        )

        perfil.sequencia_atual = (
            calcular_sequencia(
                perfil
            )
        )

    tarefas_hoje = InstanciaTarefa.objects.filter(
        familia=familia,
        data_referencia=hoje,
    )

    indicadores_semana = (
        calcular_indicadores_periodo(
            familia=familia,
            dias=7,
        )
    )

    contexto = {
        "familia": familia,
        "criancas": criancas,
        "total_criancas": len(criancas),
        "total_tarefas_hoje": tarefas_hoje.count(),
        "total_revisoes": tarefas_hoje.filter(
            status=InstanciaTarefa.Status.REVISAO
        ).count(),
        "total_pendentes": tarefas_hoje.filter(
            status=InstanciaTarefa.Status.PENDENTE
        ).count(),
        "indicadores_semana": indicadores_semana,
        "celebracao_evento": celebracao_evento,
    }

    return render(
        request,
        "usuarios/dashboard_tutor.html",
        contexto,
    )


@login_required(login_url="login")
def criancas_listar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    criancas = (
        PerfilCrianca.objects
        .filter(familia=familia)
        .select_related("usuario")
        .order_by("nome")
    )

    return render(
        request,
        "usuarios/criancas/lista.html",
        {"criancas": criancas},
    )


@login_required(login_url="login")
def crianca_criar(request):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    if request.method == "POST":
        form = CriancaForm(
            request.POST
        )

        if form.is_valid():
            form.save(
                familia=familia
            )

            messages.success(
                request,
                "Perfil da criança criado com sucesso!",
            )

            return redirect(
                "criancas_listar"
            )
    else:
        form = CriancaForm()

    return render(
        request,
        "usuarios/criancas/form.html",
        {
            "form": form,
            "titulo": "Nova criança",
            "texto_botao": "Cadastrar criança",
        },
    )


@login_required(login_url="login")
def crianca_editar(
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

    if request.method == "POST":
        form = CriancaForm(
            request.POST,
            instance=perfil,
        )

        if form.is_valid():
            form.save(
                familia=familia
            )

            messages.success(
                request,
                "Perfil atualizado com sucesso!",
            )

            return redirect(
                "criancas_listar"
            )
    else:
        form = CriancaForm(
            instance=perfil
        )

    return render(
        request,
        "usuarios/criancas/form.html",
        {
            "form": form,
            "titulo": "Editar criança",
            "texto_botao": "Salvar alterações",
        },
    )



def _gerar_codigo_convite():
    for _ in range(20):
        codigo = str(
            secrets.randbelow(
                900000
            )
            + 100000
        )

        if not ConviteTutor.objects.filter(
            codigo=codigo
        ).exists():
            return codigo

    return secrets.token_hex(4).upper()


@login_required(login_url="login")
def familia_configuracao(
    request,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    familia = obter_familia_tutor(
        request.user
    )

    convites = (
        ConviteTutor.objects
        .filter(
            familia=familia,
            ativo=True,
            usado_por__isnull=True,
            expira_em__gt=timezone.now(),
        )
        .order_by(
            "-criado_em"
        )
    )

    return render(
        request,
        "usuarios/familia/painel.html",
        {
            "familia": familia,
            "tutores": (
                familia
                .tutores
                .all()
                .order_by(
                    "first_name",
                    "username",
                )
            ),
            "convites": convites,
            "form_codigo": (
                CodigoConviteTutorForm()
            ),
        },
    )


@login_required(login_url="login")
def convite_tutor_criar(
    request,
):
    if (
        request.method != "POST"
        or request.user.tipo
        != Usuario.Tipo.TUTOR
    ):
        return redirect(
            "familia_configuracao"
        )

    familia = obter_familia_tutor(
        request.user
    )

    ConviteTutor.objects.filter(
        familia=familia,
        ativo=True,
        usado_por__isnull=True,
    ).update(
        ativo=False
    )

    convite = (
        ConviteTutor.objects.create(
            familia=familia,
            codigo=(
                _gerar_codigo_convite()
            ),
            criado_por=request.user,
            expira_em=(
                timezone.now()
                + timedelta(
                    hours=48
                )
            ),
        )
    )

    messages.success(
        request,
        (
            "Código criado. Compartilhe "
            f"{convite.codigo} com o outro responsável. "
            "Ele expira em 48 horas."
        ),
    )

    return redirect(
        "familia_configuracao"
    )


@login_required(login_url="login")
def familia_entrar_codigo(
    request,
):
    if request.user.tipo != Usuario.Tipo.TUTOR:
        return redirect("inicio")

    if request.method != "POST":
        return redirect(
            "familia_configuracao"
        )

    form = CodigoConviteTutorForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            "Informe um código válido.",
        )
        return redirect(
            "familia_configuracao"
        )

    codigo = form.cleaned_data[
        "codigo"
    ]

    convite = (
        ConviteTutor.objects
        .filter(
            codigo=codigo,
            ativo=True,
            usado_por__isnull=True,
        )
        .select_related(
            "familia"
        )
        .first()
    )

    if (
        convite is None
        or convite.expirado
    ):
        messages.error(
            request,
            (
                "Código inválido ou expirado. "
                "Peça um novo código ao responsável."
            ),
        )
        return redirect(
            "familia_configuracao"
        )

    destino = convite.familia

    if destino.tutores.filter(
        pk=request.user.pk
    ).exists():
        messages.info(
            request,
            (
                "Você já faz parte "
                "desta família."
            ),
        )
        return redirect(
            "familia_configuracao"
        )

    outras_familias = list(
        request.user
        .familias_como_tutor
        .exclude(
            pk=destino.pk
        )
    )

    for familia_atual in outras_familias:
        familia_vazia = (
            not familia_atual.criancas.exists()
            and familia_atual.tutores.count() == 1
            and familia_atual.tutores.filter(
                pk=request.user.pk
            ).exists()
        )

        if not familia_vazia:
            messages.error(
                request,
                (
                    "Sua conta já está vinculada "
                    "a outra família com dados. "
                    "Para evitar misturar famílias, "
                    "o ingresso foi bloqueado."
                ),
            )
            return redirect(
                "familia_configuracao"
            )

    # Remove as famílias vazias criadas automaticamente no primeiro login.
    for familia_atual in outras_familias:
        familia_atual.tutores.remove(
            request.user
        )

        if (
            not familia_atual.tutores.exists()
            and not familia_atual.criancas.exists()
        ):
            familia_atual.delete()

    destino.tutores.add(
        request.user
    )

    convite.usado_por = request.user
    convite.utilizado_em = timezone.now()
    convite.ativo = False

    convite.save(
        update_fields=[
            "usado_por",
            "utilizado_em",
            "ativo",
        ]
    )

    messages.success(
        request,
        (
            f"Você entrou em "
            f"{destino.nome} como responsável."
        ),
    )

    return redirect(
        "familia_configuracao"
    )


@login_required(login_url="login")
def convite_tutor_cancelar(
    request,
    convite_id,
):
    if (
        request.method != "POST"
        or request.user.tipo
        != Usuario.Tipo.TUTOR
    ):
        return redirect(
            "familia_configuracao"
        )

    familia = obter_familia_tutor(
        request.user
    )

    convite = get_object_or_404(
        ConviteTutor,
        id=convite_id,
        familia=familia,
        ativo=True,
    )

    convite.ativo = False
    convite.save(
        update_fields=[
            "ativo",
        ]
    )

    messages.success(
        request,
        "Convite cancelado.",
    )

    return redirect(
        "familia_configuracao"
    )


def service_worker_view(request):
    response = render(
        request,
        "pwa/service-worker.js",
        content_type="application/javascript",
    )

    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Service-Worker-Allowed"] = "/"

    return response


def offline_view(request):
    return render(
        request,
        "pwa/offline.html",
    )
