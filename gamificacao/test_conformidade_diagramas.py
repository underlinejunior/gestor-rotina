"""Testes de conformidade dos métodos descritos nos diagramas UML fornecidos."""
from django.test import TestCase
from django.utils import timezone
from usuarios.models import Familia, PerfilInfantil, Usuario
from .models import (Recompensa, SolicitacaoResgate, MovimentacaoPontos,
                     Habilidade, ProgressoHabilidade, Conquista, ConquistaInfantil)


class DiagramasRecompensaTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(username="uml_tutor", password="senha_uml_123")
        self.outro = Usuario.objects.create_user(username="uml_outro", password="senha_uml_123")
        self.familia = Familia.objects.create(nome="Família UML")
        self.familia.adicionar_responsavel(self.tutor)
        self.familia_outra = Familia.objects.create(nome="Outra Família UML")
        self.familia_outra.adicionar_responsavel(self.outro)
        self.crianca = PerfilInfantil.objects.create(familia=self.familia, nome="Ana", saldo_pontos=100)
        self.recompensa = Recompensa.objects.create(familia=self.familia, criada_por=self.tutor,
                                                    titulo="Passeio", custo_pontos=20)

    def test_recompensa_consulta_e_alteracao(self):
        self.assertTrue(self.recompensa.esta_disponivel())
        self.assertEqual(self.recompensa.consultar_custo(), 20)
        self.recompensa.alterar_recompensa(custo_pontos=25, titulo="Passeio ao parque")
        self.recompensa.refresh_from_db()
        self.assertEqual(self.recompensa.consultar_custo(), 25)

    def test_solicitacao_e_entrega_exigem_tutor_da_familia(self):
        pedido = SolicitacaoResgate.solicitar_resgate(self.crianca, self.recompensa)
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, 80)
        with self.assertRaises(ValueError):
            pedido.confirmar_entrega(self.outro)
        pedido.confirmar_entrega(self.tutor)
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, SolicitacaoResgate.Status.ENTREGUE)
        self.assertIsNotNone(pedido.concluido_em)
        with self.assertRaises(ValueError):
            pedido.confirmar_entrega(self.tutor)
        self.assertEqual(pedido.movimentacao_pontos.consultar_pontos(), -20)
        self.assertEqual(pedido.movimentacao_pontos.consultar_saldo(), 80)

    def test_cancelamento_por_modelo_restitui_somente_uma_vez(self):
        pedido = SolicitacaoResgate.solicitar_resgate(self.crianca, self.recompensa)
        pedido.cancelar_resgate(self.tutor)
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, 100)
        with self.assertRaises(ValueError):
            pedido.cancelar_resgate(self.tutor)

    def test_consultar_data_conquista(self):
        conquista = Conquista.objects.create(slug="uml-conquista", nome="Conquista UML", descricao="Teste")
        atribuicao = ConquistaInfantil.objects.create(crianca=self.crianca, conquista=conquista)
        self.assertEqual(atribuicao.consultar_data_desbloqueio(), atribuicao.desbloqueada_em)

    def test_progresso_habilidade_metodos_de_consulta(self):
        habilidade = Habilidade.objects.create(nome="Habilidade UML", slug="habilidade-uml")
        progresso = ProgressoHabilidade.objects.create(crianca=self.crianca, habilidade=habilidade,
                                                       experiencia_acumulada=75)
        self.assertEqual(progresso.consultar_nivel(), 2)
        self.assertEqual(progresso.calcular_progresso(), 50)

class DiagramasCriteriosTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(username="criterio_tutor", password="senha123")
        self.familia = Familia.objects.create(nome="Critérios")
        self.familia.tutores.add(self.tutor)
        self.crianca = PerfilInfantil.objects.create(familia=self.familia, nome="Maria")

    def test_rn13_verificar_criterio_conquista_primeira_missao_idempotente(self):
        from tarefas.models import TarefaAgendada
        conquista, _ = Conquista.objects.get_or_create(
            slug="primeira-missao", defaults={"nome": "Primeira missão", "descricao": "Uma tarefa"}
        )
        self.assertFalse(conquista.verificar_criterio(self.crianca))
        TarefaAgendada.objects.create(
            familia=self.familia, crianca=self.crianca, criada_por=self.tutor,
            origem=TarefaAgendada.Origem.BONUS, titulo="Uma tarefa",
            data_referencia=timezone.localdate(), status=TarefaAgendada.Status.APROVADA,
        )
        self.assertTrue(conquista.verificar_criterio(self.crianca))
        self.assertTrue(conquista.verificar_criterio(self.crianca))
        self.assertEqual(ConquistaInfantil.objects.filter(crianca=self.crianca, conquista=conquista).count(), 1)

    def test_rn05_nao_permitir_credito_de_experiencia_sem_tarefa_aprovada(self):
        from tarefas.models import TarefaAgendada
        habilidade, _ = Habilidade.objects.get_or_create(
            nome="Foco", defaults={"slug": "foco"}
        )
        progresso = ProgressoHabilidade.objects.create(crianca=self.crianca, habilidade=habilidade)
        tarefa = TarefaAgendada.objects.create(
            familia=self.familia, crianca=self.crianca, criada_por=self.tutor,
            origem=TarefaAgendada.Origem.BONUS, titulo="Teste",
            data_referencia=timezone.localdate(), status=TarefaAgendada.Status.PENDENTE,
        )
        with self.assertRaises(ValueError):
            progresso.adicionar_experiencia(5, tarefa=tarefa)
        self.assertEqual(progresso.experiencia_acumulada, 0)

    def test_rn05_adicionar_experiencia_por_tarefa_aprovada_idempotente(self):
        from tarefas.models import TarefaAgendada
        from .models import TarefaHabilidade, MovimentacaoHabilidade
        habilidade, _ = Habilidade.objects.get_or_create(
            nome="Organização", defaults={"slug": "organizacao"}
        )
        progresso = ProgressoHabilidade.objects.create(crianca=self.crianca, habilidade=habilidade)
        tarefa = TarefaAgendada.objects.create(
            familia=self.familia, crianca=self.crianca, criada_por=self.tutor,
            origem=TarefaAgendada.Origem.BONUS, titulo="Organizar materiais",
            data_referencia=timezone.localdate(), status=TarefaAgendada.Status.APROVADA,
        )
        TarefaHabilidade.objects.create(
            tarefa=tarefa, habilidade=habilidade, nome_snapshot=habilidade.nome,
            intensidade=Habilidade.Intensidade.BAIXA, experiencia_prevista=3,
        )
        self.assertEqual(progresso.adicionar_experiencia(3, tarefa=tarefa), 3)
        self.assertEqual(progresso.adicionar_experiencia(3, tarefa=tarefa), 3)
        self.assertEqual(MovimentacaoHabilidade.objects.filter(tarefa=tarefa, habilidade=habilidade).count(), 1)
        with self.assertRaises(ValueError):
            progresso.adicionar_experiencia(6, tarefa=tarefa)
