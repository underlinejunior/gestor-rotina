from datetime import date, datetime, time, timedelta
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from gamificacao.models import (
    RotinaHabilidade,
    MovimentacaoPontos,
    NotificacaoSistema,
    Habilidade,
)
from tarefas.forms import EnvioComprovanteForm
from tarefas.models import TarefaAgendada, RotinaPlanejada, PeriodoTarefa
from tarefas.services import (
    ConfiguracaoIAAusente,
    _extrair_json_ia,
    _normalizar_sugestoes_ia,
    aprovar_tarefa,
    encerrar_tarefas_antigas,
    enviar_comprovante,
    gerar_tarefas_do_dia,
    processar_lembretes,
    rejeitar_tarefa,
)
from usuarios.models import Familia, PerfilInfantil, Usuario


GIF_1X1 = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
    b"\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00"
    b"\x00\x01\x00\x01\x00\x00\x02\x02D"
    b"\x01\x00;"
)


class SugestoesIATests(SimpleTestCase):
    def test_extrair_json_aceita_cerca_markdown(self):
        dados = _extrair_json_ia(
            '```json\n[{"titulo": "Arrumar a cama"}]\n```'
        )
        self.assertEqual(dados[0]["titulo"], "Arrumar a cama")

    def test_normalizar_sugestoes_descarta_skill_invalida(self):
        sugestoes = _normalizar_sugestoes_ia(
            [
                {
                    "icone": "🛏️",
                    "titulo": "Arrumar a cama",
                    "descricao": "Organizar a cama.",
                    "pontos": 12,
                    "skills": [
                        {"slug": "organizacao", "intensidade": 3},
                        {"slug": "inexistente", "intensidade": 3},
                    ],
                }
            ],
            [
                {
                    "slug": "organizacao",
                    "nome": "Organização",
                }
            ],
        )

        self.assertEqual(len(sugestoes), 1)
        self.assertEqual(
            sugestoes[0]["skills"],
            [{"slug": "organizacao", "intensidade": 3}],
        )

    @patch.dict("os.environ", {"GEMINI_API_KEY": ""})
    def test_sugestao_ia_sem_chave_falha_de_forma_controlada(self):
        from tarefas.services import gerar_sugestao_rotina

        with self.assertRaises(ConfiguracaoIAAusente):
            gerar_sugestao_rotina(idade_crianca=8)


class BaseTarefasTestCase(TestCase):
    def setUp(self):
        self._media_dir = tempfile.TemporaryDirectory()
        self._media_override = override_settings(
            MEDIA_ROOT=self._media_dir.name
        )
        self._media_override.enable()
        self.addCleanup(self._media_override.disable)
        self.addCleanup(self._media_dir.cleanup)

        self.tutor = Usuario.objects.create_user(
            username="tutor",
            password="Senha12345",
            first_name="Responsável",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.usuario_crianca = Usuario.objects.create_user(
            username="filho",
            password="SenhaFilho123",
            first_name="Filho",
            tipo=Usuario.Tipo.CRIANCA,
        )
        self.familia = Familia.objects.create(nome="Família Teste")
        self.familia.tutores.add(self.tutor)
        self.crianca = PerfilInfantil.objects.create(
            familia=self.familia,
            nome="Filho",
            usuario=self.usuario_crianca,
            acesso_proprio=True,
        )

    def criar_rotina(self, **kwargs):
        dados = {
            "familia": self.familia,
            "crianca": self.crianca,
            "titulo": "Arrumar a cama",
            "descricao": "Organizar a cama ao acordar.",
            "pontos_base": 10,
            "frequencia": RotinaPlanejada.Frequencia.DIARIA,
            "periodo": PeriodoTarefa.MANHA,
            "lembrete_ativo": False,
            "criado_por": self.tutor,
        }
        dados.update(kwargs)
        return RotinaPlanejada.objects.create(**dados)

    def criar_tarefa(self, **kwargs):
        dados = {
            "familia": self.familia,
            "crianca": self.crianca,
            "criada_por": self.tutor,
            "origem": TarefaAgendada.Origem.BONUS,
            "titulo": "Guardar brinquedos",
            "descricao": "",
            "pontos_base": 10,
            "data_referencia": timezone.localdate(),
        }
        dados.update(kwargs)
        return TarefaAgendada.objects.create(**dados)


class RF03RotinasTests(BaseTarefasTestCase):
    """RF03 — rotinas, recorrência, horários e lembretes."""

    def test_rf03_rotina_diario_gera_em_qualquer_dia(self):
        rotina = self.criar_rotina(
            frequencia=RotinaPlanejada.Frequencia.DIARIA
        )

        self.assertTrue(rotina.deve_gerar_em(date(2026, 8, 24)))
        self.assertTrue(rotina.deve_gerar_em(date(2026, 8, 25)))

    def test_rf03_rotina_semanal_respeita_dias_configurados(self):

        rotina = self.criar_rotina(
            frequencia=RotinaPlanejada.Frequencia.SEMANAL,
            dias_semana="0,2",
        )

        self.assertTrue(rotina.deve_gerar_em(date(2026, 8, 24)))
        self.assertFalse(rotina.deve_gerar_em(date(2026, 8, 25)))
        self.assertTrue(rotina.deve_gerar_em(date(2026, 8, 26)))

    def test_rf03_lembrete_respeita_periodo_ou_horario_especifico(self):
        manha = self.criar_rotina(
            titulo="Café",
            periodo=PeriodoTarefa.MANHA,
            lembrete_ativo=True,
        )
        horario = self.criar_rotina(
            titulo="Estudo",
            periodo=PeriodoTarefa.HORARIO,
            horario=time(17, 30),
            lembrete_ativo=True,
        )

        self.assertEqual(manha.horario_lembrete, time(8, 0))
        self.assertEqual(horario.horario_lembrete, time(17, 30))


class RF04RF06GeracaoESnapshotTests(BaseTarefasTestCase):
    """RF04, RF06 e RN01 — bônus, geração automática e preservação histórica."""

    def test_rf04_tutor_cria_tarefa_bonus(self):
        self.client.force_login(self.tutor)

        resposta = self.client.post(
            reverse("tarefa_bonus_criar"),
            {
                "crianca": self.crianca.id,
                "titulo": "Ajudar na cozinha",
                "descricao": "Guardar os pratos.",
                "pontos_base": 12,
            },
        )

        self.assertRedirects(resposta, reverse("inicio"))
        tarefa = TarefaAgendada.objects.get(
            titulo="Ajudar na cozinha"
        )
        self.assertEqual(tarefa.origem, TarefaAgendada.Origem.BONUS)
        self.assertEqual(tarefa.pontos_base, 12)


    def test_rotina_pode_ser_replicada_para_todas_as_criancas_da_familia(self):
        outra = PerfilInfantil.objects.create(
            familia=self.familia,
            nome="Irmã",
        )
        self.client.force_login(self.tutor)

        resposta = self.client.post(
            reverse("rotina_criar"),
            {
                "crianca": self.crianca.id,
                "titulo": "Organizar mochila",
                "descricao": "Separar materiais.",
                "pontos_base": 10,
                "frequencia": RotinaPlanejada.Frequencia.DIARIA,
                "periodo": PeriodoTarefa.QUALQUER,
                "ativa": "on",
                "replicar_todas": "on",
            },
        )

        self.assertRedirects(resposta, reverse("rotinas_listar"))
        rotinas = RotinaPlanejada.objects.filter(
            familia=self.familia,
            titulo="Organizar mochila",
        )

        self.assertEqual(rotinas.count(), 2)
        self.assertSetEqual(
            set(rotinas.values_list("crianca_id", flat=True)),
            {self.crianca.id, outra.id},
        )

    def test_rf06_geracao_diaria_e_idempotente_e_copia_snapshot(self):
        habilidade, _ = Habilidade.objects.get_or_create(
            slug="organizacao",
            defaults={
                "nome": "Organização",
                "icone": "📋",
            },
        )
        rotina = self.criar_rotina(
            titulo="Organizar mochila",
            descricao="Separar o material escolar.",
            pontos_base=15,
            periodo=PeriodoTarefa.NOITE,
            lembrete_ativo=True,
        )
        RotinaHabilidade.objects.create(
            rotina=rotina,
            habilidade=habilidade,
            intensidade=Habilidade.Intensidade.ALTA,
        )

        dia = date(2026, 8, 25)
        primeira = gerar_tarefas_do_dia(
            familia=self.familia,
            data=dia,
        )
        segunda = gerar_tarefas_do_dia(
            familia=self.familia,
            data=dia,
        )

        self.assertEqual(primeira, 1)
        self.assertEqual(segunda, 0)

        tarefa = TarefaAgendada.objects.get(
            rotina=rotina,
            data_referencia=dia,
        )
        self.assertEqual(tarefa.titulo, "Organizar mochila")
        self.assertEqual(tarefa.pontos_base, 15)
        self.assertEqual(tarefa.periodo, PeriodoTarefa.NOITE)
        self.assertTrue(tarefa.lembrete_ativo)

        snapshot = tarefa.habilidades_tarefa.get()
        self.assertEqual(snapshot.nome_snapshot, "Organização")
        self.assertEqual(snapshot.intensidade, Habilidade.Intensidade.ALTA)
        self.assertEqual(snapshot.experiencia_prevista, 10)

    def test_rn01_edicao_da_rotina_nao_altera_tarefa_historica(self):
        rotina = self.criar_rotina(
            titulo="Título original",
            descricao="Descrição original",
            pontos_base=10,
        )
        dia = date(2026, 8, 25)
        gerar_tarefas_do_dia(familia=self.familia, data=dia)
        tarefa = TarefaAgendada.objects.get(
            rotina=rotina,
            data_referencia=dia,
        )

        rotina.titulo = "Título alterado"
        rotina.descricao = "Descrição alterada"
        rotina.pontos_base = 99
        rotina.save()

        tarefa.refresh_from_db()
        self.assertEqual(tarefa.titulo, "Título original")
        self.assertEqual(tarefa.descricao, "Descrição original")
        self.assertEqual(tarefa.pontos_base, 10)

    def test_rn01_exclusao_da_rotina_preserva_instancia_historica(self):
        rotina = self.criar_rotina()
        dia = date(2026, 8, 25)
        gerar_tarefas_do_dia(familia=self.familia, data=dia)
        tarefa = TarefaAgendada.objects.get(
            rotina=rotina,
            data_referencia=dia,
        )

        rotina.delete()

        tarefa.refresh_from_db()
        self.assertIsNone(tarefa.rotina)
        self.assertEqual(tarefa.titulo, "Arrumar a cama")


class RF07RF08RF09FluxoTarefaTests(BaseTarefasTestCase):
    """RF07, RF08 e RF09 — visão da criança, evidência e revisão do Tutor."""

    def test_rf07_crianca_visualiza_somente_as_proprias_tarefas(self):
        outra = PerfilInfantil.objects.create(
            familia=self.familia,
            nome="Irmã",
        )
        minha = self.criar_tarefa(titulo="Minha tarefa")
        TarefaAgendada.objects.create(
            familia=self.familia,
            crianca=outra,
            criada_por=self.tutor,
            origem=TarefaAgendada.Origem.BONUS,
            titulo="Tarefa da irmã",
            pontos_base=10,
            data_referencia=timezone.localdate(),
        )

        self.client.force_login(self.usuario_crianca)
        resposta = self.client.get(reverse("minhas_tarefas"))

        self.assertEqual(resposta.status_code, 200)
        tarefas = list(resposta.context["tarefas"])
        self.assertIn(minha, tarefas)
        self.assertEqual(len(tarefas), 1)

    def test_rnf02_formulario_de_foto_solicita_camera_traseira(self):
        widget = EnvioComprovanteForm.base_fields["foto"].widget

        self.assertEqual(widget.attrs.get("accept"), "image/*")
        self.assertEqual(widget.attrs.get("capture"), "environment")

    def test_rf08_envio_de_evidencia_move_tarefa_para_revisao(self):
        tarefa = self.criar_tarefa()
        foto = SimpleUploadedFile(
            "evidencia.gif",
            GIF_1X1,
            content_type="image/gif",
        )

        enviar_comprovante(tarefa, foto)
        tarefa.refresh_from_db()

        self.assertEqual(tarefa.status, TarefaAgendada.Status.REVISAO)
        self.assertTrue(bool(tarefa.foto))
        self.assertIsNotNone(tarefa.enviada_em)
        self.assertIsNone(tarefa.pontos_concedidos)

    def test_rf09_aprovacao_concede_pontos_e_registra_revisor(self):
        tarefa = self.criar_tarefa(
            status=TarefaAgendada.Status.REVISAO,
        )

        aprovar_tarefa(
            tarefa=tarefa,
            tutor=self.tutor,
            pontos=12,
            feedback="Muito bem!",
        )

        tarefa.refresh_from_db()
        self.crianca.refresh_from_db()

        self.assertEqual(tarefa.status, TarefaAgendada.Status.APROVADA)
        self.assertEqual(tarefa.pontos_concedidos, 12)
        self.assertEqual(tarefa.revisada_por, self.tutor)
        self.assertEqual(tarefa.feedback_tutor, "Muito bem!")
        self.assertEqual(self.crianca.saldo_pontos, 12)
        self.assertEqual(self.crianca.pontos_experiencia, 12)
        self.assertEqual(
            MovimentacaoPontos.objects.get(tarefa=tarefa).tipo,
            MovimentacaoPontos.Tipo.APROVACAO,
        )

    def test_rf09_rejeicao_nao_concede_pontos_e_permite_novo_envio(self):
        tarefa = self.criar_tarefa(
            status=TarefaAgendada.Status.REVISAO,
        )

        rejeitar_tarefa(
            tarefa=tarefa,
            tutor=self.tutor,
            feedback="Refaça a foto.",
        )
        tarefa.refresh_from_db()
        self.crianca.refresh_from_db()

        self.assertEqual(tarefa.status, TarefaAgendada.Status.REJEITADA)
        self.assertEqual(tarefa.pontos_concedidos, 0)
        self.assertEqual(self.crianca.saldo_pontos, 0)
        self.assertTrue(tarefa.pode_enviar_comprovante)

    def test_rn03_procrastinacao_e_identificada_apos_oito_horas(self):
        tarefa = self.criar_tarefa()
        criada_em = timezone.now() - timedelta(hours=9)

        TarefaAgendada.objects.filter(pk=tarefa.pk).update(
            criada_em=criada_em,
            enviada_em=timezone.now(),
        )
        tarefa.refresh_from_db()

        self.assertTrue(tarefa.procrastinou)


class RF10NotificacoesEPenalidadeTests(BaseTarefasTestCase):
    """RF10 e RN04 — lembretes, encerramento e penalidade."""

    def test_rf10_lembrete_cria_notificacao_para_crianca_com_acesso_proprio(self):
        tarefa = self.criar_tarefa(
            titulo="Escovar os dentes",
            periodo=PeriodoTarefa.HORARIO,
            horario=time(8, 0),
            lembrete_ativo=True,
        )
        agora = timezone.make_aware(
            datetime.combine(
                timezone.localdate(),
                time(8, 5),
            ),
            timezone.get_current_timezone(),
        )

        criadas = processar_lembretes(
            familia=self.familia,
            agora=agora,
        )

        self.assertEqual(criadas, 1)
        notificacao = NotificacaoSistema.objects.get(
            usuario_destino=self.usuario_crianca,
            tarefa=tarefa,
        )
        self.assertEqual(
            notificacao.tipo,
            NotificacaoSistema.Tipo.LEMBRETE_TAREFA,
        )

    def test_rn04_tarefa_antiga_nao_realizada_desconta_metade_arredondada_para_cima(self):
        self.crianca.saldo_pontos = 20
        self.crianca.pontos_experiencia = 20
        self.crianca.save()

        tarefa = self.criar_tarefa(
            pontos_base=5,
            data_referencia=timezone.localdate() - timedelta(days=1),
            status=TarefaAgendada.Status.PENDENTE,
        )

        encerradas = encerrar_tarefas_antigas(
            familia=self.familia,
            hoje=timezone.localdate(),
        )

        tarefa.refresh_from_db()
        self.crianca.refresh_from_db()
        movimento = MovimentacaoPontos.objects.get(tarefa=tarefa)

        self.assertEqual(encerradas, 1)
        self.assertEqual(
            tarefa.status,
            TarefaAgendada.Status.NAO_REALIZADA,
        )
        self.assertEqual(movimento.pontos, -3)
        self.assertEqual(self.crianca.saldo_pontos, 17)
        self.assertEqual(self.crianca.pontos_experiencia, 20)
        self.assertTrue(
            NotificacaoSistema.objects.filter(
                usuario_destino=self.tutor,
                tarefa=tarefa,
                tipo=NotificacaoSistema.Tipo.TAREFA_NAO_REALIZADA,
            ).exists()
        )

    def test_penalidade_nao_e_aplicada_duas_vezes(self):
        self.crianca.saldo_pontos = 10
        self.crianca.pontos_experiencia = 10
        self.crianca.save()

        tarefa = self.criar_tarefa(
            pontos_base=10,
            data_referencia=timezone.localdate() - timedelta(days=1),
        )

        encerrar_tarefas_antigas(
            familia=self.familia,
            hoje=timezone.localdate(),
        )
        primeira = MovimentacaoPontos.objects.get(tarefa=tarefa)


        encerrar_tarefas_antigas(
            familia=self.familia,
            hoje=timezone.localdate(),
        )

        self.crianca.refresh_from_db()
        self.assertEqual(MovimentacaoPontos.objects.filter(tarefa=tarefa).count(), 1)
        self.assertEqual(primeira.pontos, -5)
        self.assertEqual(self.crianca.saldo_pontos, 5)


class RelatorioEPermissoesTests(BaseTarefasTestCase):
    """Objetivo específico de visão estruturada e isolamento de dados."""

    def test_relatorio_semanal_consolida_indicadores_da_crianca(self):
        hoje = timezone.localdate()
        inicio = hoje - timedelta(days=hoje.weekday())

        self.criar_tarefa(
            titulo="Aprovada",
            data_referencia=inicio,
            status=TarefaAgendada.Status.APROVADA,
            pontos_concedidos=10,
        )
        self.criar_tarefa(
            titulo="Não realizada",
            data_referencia=inicio + timedelta(days=1),
            status=TarefaAgendada.Status.NAO_REALIZADA,
        )

        self.client.force_login(self.tutor)
        resposta = self.client.get(
            reverse(
                "relatorio_semanal_crianca",
                args=[self.crianca.id],
            ),
            {"inicio": inicio.isoformat()},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["aprovadas"], 1)
        self.assertEqual(resposta.context["nao_realizadas"], 1)
        self.assertEqual(resposta.context["taxa_conclusao"], 50)

    def test_tutor_nao_acessa_relatorio_de_crianca_de_outra_familia(self):
        outro_tutor = Usuario.objects.create_user(
            username="outro",
            password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        outra_familia = Familia.objects.create(nome="Outra Família")
        outra_familia.tutores.add(outro_tutor)

        self.client.force_login(outro_tutor)
        resposta = self.client.get(
            reverse(
                "relatorio_semanal_crianca",
                args=[self.crianca.id],
            )
        )

        self.assertEqual(resposta.status_code, 404)


class AutorizacaoServicosTarefaTests(BaseTarefasTestCase):
    """Uma chamada direta aos serviços não pode contornar a família."""

    def test_tutor_de_outra_familia_nao_aprova(self):
        estranho = Usuario.objects.create_user(
            username="outro_tutor_aprovar", password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        outra_familia = Familia.objects.create(nome="Outra família")
        outra_familia.tutores.add(estranho)
        tarefa = self.criar_tarefa(status=TarefaAgendada.Status.REVISAO)
        with self.assertRaisesMessage(ValueError, "não pertence à família"):
            aprovar_tarefa(tarefa=tarefa, tutor=estranho, pontos=10)
        tarefa.refresh_from_db()
        self.crianca.refresh_from_db()
        self.assertEqual(tarefa.status, TarefaAgendada.Status.REVISAO)
        self.assertEqual(self.crianca.saldo_pontos, 0)
        self.assertFalse(MovimentacaoPontos.objects.filter(tarefa=tarefa).exists())

    def test_tutor_de_outra_familia_nao_rejeita(self):
        estranho = Usuario.objects.create_user(
            username="outro_tutor_rejeitar", password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        tarefa = self.criar_tarefa(status=TarefaAgendada.Status.REVISAO)
        with self.assertRaisesMessage(ValueError, "não pertence à família"):
            rejeitar_tarefa(tarefa=tarefa, tutor=estranho, feedback="Invasão")
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, TarefaAgendada.Status.REVISAO)
        self.assertEqual(tarefa.feedback_tutor, "")
