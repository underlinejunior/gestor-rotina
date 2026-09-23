from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from gamificacao.models import (
    Conquista,
    ConquistaCrianca,
    InstanciaTarefaSkill,
    MovimentoPontos,
    MovimentoSkill,
    ProgressoSkill,
    Recompensa,
    ResgateRecompensa,
    Skill,
)
from gamificacao.services import (
    avaliar_conquistas,
    calcular_sequencia,
    cancelar_resgate,
    montar_painel_habilidades,
    registrar_xp_skills_aprovacao,
    resgatar_recompensa,
)
from tarefas.models import InstanciaTarefa
from usuarios.models import Familia, PerfilCrianca, Usuario


class BaseGamificacaoTestCase(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(
            username="tutor",
            password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Teste")
        self.familia.tutores.add(self.tutor)
        self.crianca = PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Criança",
        )

    def criar_tarefa(self, **kwargs):
        dados = {
            "familia": self.familia,
            "crianca": self.crianca,
            "criada_por": self.tutor,
            "origem": InstanciaTarefa.Origem.BONUS,
            "titulo": "Tarefa",
            "pontos_base": 10,
            "data_referencia": timezone.localdate(),
            "status": InstanciaTarefa.Status.PENDENTE,
        }
        dados.update(kwargs)
        return InstanciaTarefa.objects.create(**dados)


class GamificacaoSkillsTests(BaseGamificacaoTestCase):
    """Objetivo de gamificação — Skills e progressão sem caráter diagnóstico."""

    def test_intensidade_da_skill_mapeia_para_xp_previsto(self):
        self.assertEqual(Skill.xp_por_impacto(Skill.Impacto.LEVE), 3)
        self.assertEqual(Skill.xp_por_impacto(Skill.Impacto.MEDIO), 6)
        self.assertEqual(Skill.xp_por_impacto(Skill.Impacto.FORTE), 10)

    def test_aprovacao_de_skill_registra_xp_uma_unica_vez(self):
        skill, _ = Skill.objects.get_or_create(
            slug="autonomia",
            defaults={
                "nome": "Autonomia",
                "icone": "🌱",
            },
        )
        tarefa = self.criar_tarefa(
            status=InstanciaTarefa.Status.APROVADA,
        )
        InstanciaTarefaSkill.objects.create(
            tarefa=tarefa,
            skill=skill,
            nome_snapshot="Autonomia",
            icone_snapshot="🌱",
            impacto=Skill.Impacto.FORTE,
            xp_planejado=10,
        )

        registrar_xp_skills_aprovacao(tarefa)
        registrar_xp_skills_aprovacao(tarefa)

        progresso = ProgressoSkill.objects.get(
            crianca=self.crianca,
            skill=skill,
        )
        self.assertEqual(progresso.xp_total, 10)
        self.assertEqual(
            MovimentoSkill.objects.filter(
                tarefa=tarefa,
                skill=skill,
            ).count(),
            1,
        )

    def test_painel_apresenta_skill_sem_inferir_valor_alem_do_xp_registrado(self):
        skill, _ = Skill.objects.get_or_create(
            slug="organizacao",
            defaults={
                "nome": "Organização",
                "icone": "📋",
                "ordem": 1,
            },
        )
        ProgressoSkill.objects.create(
            crianca=self.crianca,
            skill=skill,
            xp_total=65,
        )

        painel = montar_painel_habilidades(self.crianca)
        item = next(
            registro
            for registro in painel
            if registro["skill"].id == skill.id
        )

        self.assertEqual(item["xp_total"], 65)
        self.assertEqual(item["nivel"], 2)
        self.assertEqual(item["titulo_nivel"], "Praticando")


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
        self.assertEqual(resgate.status, ResgateRecompensa.Status.SOLICITADO)

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
            ResgateRecompensa.objects.filter(
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
            ResgateRecompensa.Status.CANCELADO,
        )
        self.assertTrue(
            MovimentoPontos.objects.filter(
                crianca=self.crianca,
                tipo=MovimentoPontos.Tipo.AJUSTE,
                pontos=50,
            ).exists()
        )


class StreakEConquistasTests(BaseGamificacaoTestCase):
    """Gamificação — sequência e conquistas."""

    def test_streak_ignora_dias_sem_tarefa(self):
        hoje = timezone.localdate()
        self.criar_tarefa(
            titulo="Hoje",
            data_referencia=hoje,
            status=InstanciaTarefa.Status.APROVADA,
        )
        self.criar_tarefa(
            titulo="Dois dias atrás",
            data_referencia=hoje - timedelta(days=2),
            status=InstanciaTarefa.Status.APROVADA,
        )

        self.assertEqual(calcular_sequencia(self.crianca), 2)

    def test_tarefa_nao_realizada_interrompe_streak(self):
        hoje = timezone.localdate()
        self.criar_tarefa(
            titulo="Hoje",
            data_referencia=hoje,
            status=InstanciaTarefa.Status.APROVADA,
        )
        self.criar_tarefa(
            titulo="Ontem",
            data_referencia=hoje - timedelta(days=1),
            status=InstanciaTarefa.Status.NAO_REALIZADA,
        )
        self.criar_tarefa(
            titulo="Antes de ontem",
            data_referencia=hoje - timedelta(days=2),
            status=InstanciaTarefa.Status.APROVADA,
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
            status=InstanciaTarefa.Status.APROVADA,
        )

        avaliar_conquistas(self.crianca)

        self.assertTrue(
            ConquistaCrianca.objects.filter(
                crianca=self.crianca,
                conquista=conquista,
            ).exists()
        )
