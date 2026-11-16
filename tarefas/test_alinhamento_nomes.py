from django.apps import apps
from django.test import SimpleTestCase
from tarefas.models import RotinaPlanejada, TarefaAgendada, SugestaoAtividade
from gamificacao.models import (Habilidade, TarefaHabilidade, ProgressoHabilidade,
                                 MovimentacaoPontos, SolicitacaoResgate, ConquistaInfantil)


class NomesModelosDjangoTests(SimpleTestCase):
    def test_modelos_registrados_com_nomes_do_diagrama(self):
        for modelo in (RotinaPlanejada, TarefaAgendada, SugestaoAtividade,
                       Habilidade, TarefaHabilidade, ProgressoHabilidade,
                       MovimentacaoPontos, SolicitacaoResgate, ConquistaInfantil):
            with self.subTest(modelo=modelo.__name__):
                self.assertIs(apps.get_model(modelo._meta.app_label, modelo.__name__), modelo)
                self.assertEqual(modelo._meta.object_name, modelo.__name__)
