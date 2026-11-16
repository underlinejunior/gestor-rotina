from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from gamificacao.models import (
    Conquista,
    ConquistaInfantil,
    TarefaHabilidade,
    MovimentacaoPontos,
    MovimentacaoHabilidade,
    ProgressoHabilidade,
    Recompensa,
    SolicitacaoResgate,
    Habilidade,
)
from gamificacao.services import (
    avaliar_conquistas,
    calcular_sequencia,
    calcular_sequencia_constancia,
    cancelar_resgate,
    montar_painel_habilidades,
    registrar_xp_habilidades_aprovacao,
    resgatar_recompensa,
)
from tarefas.models import RotinaPlanejada, TarefaAgendada
from usuarios.models import Familia, PerfilInfantil, Usuario


class BaseGamificacaoTestCase(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(
            username="tutor",
            password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Teste")
        self.familia.tutores.add(self.tutor)
        self.crianca = PerfilInfantil.objects.create(
            familia=self.familia,
            nome="Criança",
        )

    def criar_tarefa(self, **kwargs):
        dados = {
            "familia": self.familia,
            "crianca": self.crianca,
            "criada_por": self.tutor,
            "origem": TarefaAgendada.Origem.BONUS,
            "titulo": "Tarefa",
            "pontos_base": 10,
            "data_referencia": timezone.localdate(),
            "status": TarefaAgendada.Status.PENDENTE,
        }
        dados.update(kwargs)
        return TarefaAgendada.objects.create(**dados)


class GamificacaoSkillsTests(BaseGamificacaoTestCase):
    """Objetivo de gamificação — Skills e progressão sem caráter diagnóstico."""

    def test_intensidade_da_skill_mapeia_para_xp_previsto(self):
        self.assertEqual(Habilidade.calcular_experiencia(Habilidade.Intensidade.BAIXA), 3)
        self.assertEqual(Habilidade.calcular_experiencia(Habilidade.Intensidade.MEDIA), 6)
        self.assertEqual(Habilidade.calcular_experiencia(Habilidade.Intensidade.ALTA), 10)

    def test_aprovacao_de_skill_registra_xp_uma_unica_vez(self):
        habilidade, _ = Habilidade.objects.get_or_create(
            slug="autonomia",
            defaults={
                "nome": "Autonomia",
                "icone": "🌱",
            },
        )
        tarefa = self.criar_tarefa(
            status=TarefaAgendada.Status.APROVADA,
        )
        TarefaHabilidade.objects.create(
            tarefa=tarefa,
            habilidade=habilidade,
            nome_snapshot="Autonomia",
            icone_snapshot="🌱",
            intensidade=Habilidade.Intensidade.ALTA,
            experiencia_prevista=10,
        )

        registrar_xp_habilidades_aprovacao(tarefa)
        registrar_xp_habilidades_aprovacao(tarefa)

        progresso = ProgressoHabilidade.objects.get(
            crianca=self.crianca,
            habilidade=habilidade,
        )
        self.assertEqual(progresso.experiencia_acumulada, 10)
        self.assertEqual(
            MovimentacaoHabilidade.objects.filter(
                tarefa=tarefa,
                habilidade=habilidade,
            ).count(),
            1,
        )

    def test_painel_apresenta_skill_sem_inferir_valor_alem_do_xp_registrado(self):
        habilidade, _ = Habilidade.objects.get_or_create(
            slug="organizacao",
            defaults={
                "nome": "Organização",
                "icone": "📋",
                "ordem": 1,
            },
        )
        ProgressoHabilidade.objects.create(
            crianca=self.crianca,
            habilidade=habilidade,
            experiencia_acumulada=65,
        )

        painel = montar_painel_habilidades(self.crianca)
        item = next(
            registro
            for registro in painel
            if registro["habilidade"].id == habilidade.id
        )

        self.assertEqual(item["experiencia_acumulada"], 65)
        self.assertEqual(item["nivel"], 2)
        self.assertEqual(item["titulo_nivel"], "Praticando")


class ConstanciaPorRotinaTests(BaseGamificacaoTestCase):
    def setUp(self):
        super().setUp()
        self.habilidade, _ = Habilidade.objects.get_or_create(
            slug="constancia",
            defaults={"nome": "Constância", "icone": "🔁"},
        )
        self.rotina = RotinaPlanejada.objects.create(
            familia=self.familia,
            crianca=self.crianca,
            criado_por=self.tutor,
            titulo="Ler diariamente",
            frequencia=RotinaPlanejada.Frequencia.DIARIA,
        )

    def aprovar_no_dia(self, dia, rotina=None):
        tarefa = self.criar_tarefa(
            titulo="Ler diariamente",
            origem=TarefaAgendada.Origem.ROTINA,
            rotina=rotina or self.rotina,
            data_referencia=dia,
            status=TarefaAgendada.Status.APROVADA,
        )
        TarefaHabilidade.objects.create(
            tarefa=tarefa,
            habilidade=self.habilidade,
            nome_snapshot="Constância",
            intensidade=Habilidade.Intensidade.ALTA,
            experiencia_prevista=10,
        )
        registrar_xp_habilidades_aprovacao(tarefa)
        return tarefa

    def test_mesma_rotina_mais_de_um_dia_soma_um_por_dia_sem_xp(self):
        hoje = timezone.localdate()
        self.aprovar_no_dia(hoje - timedelta(days=1))
        self.aprovar_no_dia(hoje)
        self.assertEqual(calcular_sequencia_constancia(self.crianca), 2)
        item = next(
            x for x in montar_painel_habilidades(self.crianca)
            if x["habilidade"].slug == "constancia"
        )
        self.assertEqual(item["sequencia_constancia"], 2)
        self.assertEqual(item["experiencia_acumulada"], 0)

    def test_duas_aprovacoes_no_mesmo_dia_nao_duplicam(self):
        hoje = timezone.localdate()
        tarefa = self.aprovar_no_dia(hoje)
        registrar_xp_habilidades_aprovacao(tarefa)
        self.assertEqual(calcular_sequencia_constancia(self.crianca), 1)
        self.assertEqual(
            MovimentacaoHabilidade.objects.filter(tarefa=tarefa).count(), 1
        )

    def test_dia_sem_aprovacao_interrompe_sequencia(self):
        hoje = timezone.localdate()
        self.aprovar_no_dia(hoje - timedelta(days=2))
        self.assertEqual(calcular_sequencia_constancia(self.crianca), 0)
        self.aprovar_no_dia(hoje)
        self.assertEqual(calcular_sequencia_constancia(self.crianca), 1)

    def test_rotinas_diferentes_nao_se_somam(self):
        hoje = timezone.localdate()
        outra = RotinaPlanejada.objects.create(
            familia=self.familia, crianca=self.crianca,
            criado_por=self.tutor, titulo="Arrumar cama",
            frequencia=RotinaPlanejada.Frequencia.DIARIA,
        )
        self.aprovar_no_dia(hoje - timedelta(days=1))
        self.aprovar_no_dia(hoje, rotina=outra)
        self.assertEqual(calcular_sequencia_constancia(self.crianca), 1)


class PontosAvatarERecompensasTests(BaseGamificacaoTestCase):
    """Gamificação — saldo, XP histórico e loja de recompensas."""

    def test_nivel_do_avatar_usa_xp_historico_e_nao_cai_ao_gastar_saldo(self):
        self.crianca.saldo_pontos = 170
        self.crianca.pontos_experiencia = 170
        self.crianca.save()

        recompensa = Recompensa.objects.create(
            familia=self.familia,
            titulo="Passeio",
            custo_pontos=100,
            criada_por=self.tutor,
        )

        nivel_antes = self.crianca.avatar_nivel
        resgate = resgatar_recompensa(
            perfil=self.crianca,
            recompensa=recompensa,
        )

        self.crianca.refresh_from_db()

        self.assertEqual(nivel_antes, 3)
        self.assertEqual(self.crianca.saldo_pontos, 70)
        self.assertEqual(self.crianca.pontos_experiencia, 170)
        self.assertEqual(self.crianca.avatar_nivel, 3)
        self.assertEqual(resgate.status, SolicitacaoResgate.Status.SOLICITADO)
        self.assertEqual(resgate.movimentacao_pontos.resgate_id, resgate.pk)
        self.assertEqual(resgate.movimentacoes.count(), 1)

    def test_resgate_sem_saldo_suficiente_e_bloqueado(self):
        self.crianca.saldo_pontos = 20
        self.crianca.save()

        recompensa = Recompensa.objects.create(
            familia=self.familia,
            titulo="Filme",
            custo_pontos=80,
            criada_por=self.tutor,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Faltam 60 ponto(s)",
        ):
            resgatar_recompensa(
                perfil=self.crianca,
                recompensa=recompensa,
            )

        self.assertFalse(
            SolicitacaoResgate.objects.filter(
                crianca=self.crianca
            ).exists()
        )

    def test_cancelamento_de_resgate_devolve_pontos(self):
        self.crianca.saldo_pontos = 100
        self.crianca.pontos_experiencia = 100
        self.crianca.save()

        recompensa = Recompensa.objects.create(
            familia=self.familia,
            titulo="Brincadeira",
            custo_pontos=50,
            criada_por=self.tutor,
        )
        resgate = resgatar_recompensa(
            perfil=self.crianca,
            recompensa=recompensa,
        )

        cancelar_resgate(
            resgate=resgate,
            tutor=self.tutor,
        )

        self.crianca.refresh_from_db()
        resgate.refresh_from_db()

        self.assertEqual(self.crianca.saldo_pontos, 100)
        self.assertEqual(self.crianca.pontos_experiencia, 100)
        self.assertEqual(
            resgate.status,
            SolicitacaoResgate.Status.CANCELADO,
        )
        self.assertTrue(
            MovimentacaoPontos.objects.filter(
                crianca=self.crianca,
                tipo=MovimentacaoPontos.Tipo.AJUSTE,
                pontos=50,
            ).exists()
        )
        movimentos = list(resgate.movimentacoes.order_by("criado_em"))
        self.assertEqual(len(movimentos), 2)
        self.assertCountEqual([m.pontos for m in movimentos], [-50, 50])
        with self.assertRaisesMessage(ValueError, "Apenas resgates pendentes"):
            cancelar_resgate(resgate=resgate, tutor=self.tutor)
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, 100)


class StreakEConquistasTests(BaseGamificacaoTestCase):
    """Gamificação — sequência e conquistas."""

    def test_streak_ignora_dias_sem_tarefa(self):
        hoje = timezone.localdate()
        self.criar_tarefa(
            titulo="Hoje",
            data_referencia=hoje,
            status=TarefaAgendada.Status.APROVADA,
        )
        self.criar_tarefa(
            titulo="Dois dias atrás",
            data_referencia=hoje - timedelta(days=2),
            status=TarefaAgendada.Status.APROVADA,
        )

        self.assertEqual(calcular_sequencia(self.crianca), 2)

    def test_tarefa_nao_realizada_interrompe_streak(self):
        hoje = timezone.localdate()
        self.criar_tarefa(
            titulo="Hoje",
            data_referencia=hoje,
            status=TarefaAgendada.Status.APROVADA,
        )
        self.criar_tarefa(
            titulo="Ontem",
            data_referencia=hoje - timedelta(days=1),
            status=TarefaAgendada.Status.NAO_REALIZADA,
        )
        self.criar_tarefa(
            titulo="Antes de ontem",
            data_referencia=hoje - timedelta(days=2),
            status=TarefaAgendada.Status.APROVADA,
        )

        self.assertEqual(calcular_sequencia(self.crianca), 1)

    def test_primeira_tarefa_aprovada_desbloqueia_conquista(self):
        conquista, _ = Conquista.objects.get_or_create(
            slug="primeira-missao",
            defaults={
                "nome": "Primeiros Passos",
                "descricao": "Concluir a primeira tarefa.",
                "icone": "🌟",
            },
        )
        self.criar_tarefa(
            status=TarefaAgendada.Status.APROVADA,
        )

        avaliar_conquistas(self.crianca)

        self.assertTrue(
            ConquistaInfantil.objects.filter(
                crianca=self.crianca,
                conquista=conquista,
            ).exists()
        )


class AutorizacaoServicosResgateTests(BaseGamificacaoTestCase):
    """Cancelamento protegido por vínculo de tutela no próprio serviço."""

    def test_tutor_de_outra_familia_nao_cancela_resgate(self):
        outro = Usuario.objects.create_user(
            username="tutor_externo", password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        outra_familia = Familia.objects.create(nome="Família externa")
        outra_familia.tutores.add(outro)
        recompensa = Recompensa.objects.create(
            familia=self.familia,
            criada_por=self.tutor,
            titulo="Passeio",
            custo_pontos=10,
        )
        self.crianca.saldo_pontos = 30
        self.crianca.save(update_fields=["saldo_pontos"])
        resgate = resgatar_recompensa(perfil=self.crianca, recompensa=recompensa)
        self.crianca.refresh_from_db()
        saldo_antes = self.crianca.saldo_pontos
        with self.assertRaisesMessage(ValueError, "não pertence à família"):
            cancelar_resgate(resgate=resgate, tutor=outro)
        self.crianca.refresh_from_db()
        resgate.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, saldo_antes)
        self.assertEqual(resgate.status, SolicitacaoResgate.Status.SOLICITADO)
        self.assertEqual(MovimentacaoPontos.objects.filter(resgate=resgate).count(), 1)
