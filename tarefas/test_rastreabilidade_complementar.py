"""Testes adicionais vinculados aos diagramas e RF/RN originais (não mudam os requisitos)."""
from datetime import date, timedelta
from django.test import SimpleTestCase
from django.utils import timezone
from django.urls import reverse
from tarefas.tests import BaseTarefasTestCase
from tarefas.forms import RotinaPlanejadaForm
from tarefas.models import RotinaPlanejada, TarefaAgendada, SugestaoAtividade
from gamificacao.models import MovimentacaoPontos
from gamificacao.models import dados_nivel_habilidade
from usuarios.models import Familia, PerfilInfantil, Usuario


class RastreabilidadeModelosTests(BaseTarefasTestCase):
    def test_rf04_alterar_planejamento_preserva_campos_e_bloqueia_troca_de_familia(self):
        rotina = self.criar_rotina()
        outra = Familia.objects.create(nome="Outra")
        rotina.alterar_planejamento(titulo="Nova tarefa")
        rotina.refresh_from_db()
        self.assertEqual(rotina.titulo, "Nova tarefa")
        with self.assertRaises(ValueError):
            rotina.alterar_planejamento(familia=outra)
        rotina.refresh_from_db()
        self.assertEqual(rotina.familia_id, self.familia.pk)

    def test_rf05_sugestao_persistida_na_rotina_e_replicacao(self):
        sugestao = SugestaoAtividade.objects.create(
            titulo="Sugestão inédita", categoria="ESTUDOS",
            idade_minima=7, idade_maxima=12, ativa=True,
        )
        rotina = self.criar_rotina(sugestao_origem=sugestao)
        self.assertEqual(rotina.sugestao_origem_id, sugestao.pk)
        outro = PerfilInfantil.objects.create(familia=self.familia, nome="Irmão")
        copia = rotina.replicar_rotina(outro)
        self.assertEqual(copia.sugestao_origem_id, sugestao.pk)
        self.assertEqual(copia.familia_id, self.familia.pk)

    def test_rf05_api_filtra_sugestoes_por_idade_e_por_familia(self):
        from datetime import date
        hoje = timezone.localdate()
        self.crianca.data_nascimento = date(hoje.year - 8, hoje.month, hoje.day)
        self.crianca.save(update_fields=["data_nascimento"])
        SugestaoAtividade.objects.create(titulo="Para oito", categoria="ESTUDOS", idade_minima=7, idade_maxima=9)
        SugestaoAtividade.objects.create(titulo="Para quinze", categoria="ESTUDOS", idade_minima=14, idade_maxima=17)
        self.client.force_login(self.tutor)
        resposta = self.client.get(reverse("sugestoes_tarefas"), {"crianca_id": str(self.crianca.pk)})
        self.assertEqual(resposta.status_code, 200)
        conteudo = str(resposta.content)
        self.assertIn("Para oito", conteudo)
        self.assertNotIn("Para quinze", conteudo)
        outra_familia = Familia.objects.create(nome="Outra família")
        outra_crianca = PerfilInfantil.objects.create(familia=outra_familia, nome="Outra criança")
        resposta = self.client.get(reverse("sugestoes_tarefas"), {"crianca_id": str(outra_crianca.pk)})
        self.assertEqual(resposta.status_code, 404)

    def test_rf07_criar_bonus_so_por_tutor_da_familia(self):
        bonus = TarefaAgendada.criar_tarefa_bonus(
            tutor=self.tutor, crianca=self.crianca, titulo="Bônus de hoje")
        self.assertEqual(bonus.origem, TarefaAgendada.Origem.BONUS)
        self.assertIsNone(bonus.rotina_id)
        intruso = Usuario.objects.create_user(username="intruso_teste", password="senha", tipo=Usuario.Tipo.TUTOR)
        with self.assertRaises(ValueError):
            TarefaAgendada.criar_tarefa_bonus(tutor=intruso, crianca=self.crianca, titulo="Invasão")

    def test_rn14_em_revisao_nao_recebe_penalidade_por_prazo(self):
        from tarefas.services import encerrar_tarefas_antigas
        ontem = timezone.localdate() - timedelta(days=1)
        tarefa = self.criar_tarefa(data_referencia=ontem, status=TarefaAgendada.Status.REVISAO)
        quantidade = encerrar_tarefas_antigas(familia=self.familia)
        self.assertEqual(quantidade, 0)
        tarefa.refresh_from_db()
        self.assertEqual(tarefa.status, TarefaAgendada.Status.REVISAO)
        self.assertFalse(MovimentacaoPontos.objects.filter(tarefa=tarefa).exists())
        with self.assertRaises(ValueError):
            tarefa.marcar_nao_realizada()

    def test_rn03_encerramento_por_metodo_usa_servico_sem_duplicar(self):
        ontem = timezone.localdate() - timedelta(days=1)
        tarefa = self.criar_tarefa(data_referencia=ontem, pontos_base=11)
        self.assertTrue(tarefa.marcar_nao_realizada())
        self.assertEqual(MovimentacaoPontos.objects.filter(tarefa=tarefa).count(), 1)
        with self.assertRaises(ValueError):
            tarefa.marcar_nao_realizada()
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, -6)

    def test_rf04_formulario_sugestao_aceita_uuid_valido(self):
        sugestao = SugestaoAtividade.objects.create(titulo="Teste UUID", categoria="ESTUDOS")
        form = RotinaPlanejadaForm(familia=self.familia)
        self.assertIn("sugestao_origem_id", form.fields)
        self.assertFalse(form.fields["sugestao_origem_id"].required)
        self.assertEqual(form.fields["sugestao_origem_id"].clean(str(sugestao.pk)), sugestao.pk)


class LimitesHabilidadesTests(SimpleTestCase):
    def test_rn12_limites_cinco_niveis_e_teto_250(self):
        limites = [(0, 1), (49, 1), (50, 2), (99, 2), (100, 3),
                   (149, 3), (150, 4), (199, 4), (200, 5), (249, 5),
                   (250, 5), (500, 5)]
        for xp, nivel in limites:
            with self.subTest(xp=xp):
                self.assertEqual(dados_nivel_habilidade(xp)["nivel"], nivel)
        self.assertTrue(dados_nivel_habilidade(250)["concluido"])
        self.assertEqual(dados_nivel_habilidade(999)["xp_exibido"], 250)
