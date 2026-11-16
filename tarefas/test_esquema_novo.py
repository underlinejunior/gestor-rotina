import uuid
from django.test import TestCase
from django.utils import timezone
from usuarios.models import Usuario, Familia, PerfilInfantil
from .models import RotinaPlanejada, TarefaAgendada


class TarefasNovasTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(username='tutor_r', password='senha_forte_123')
        self.familia = Familia.objects.create(nome='Família')
        self.familia.adicionar_responsavel(self.tutor)
        self.crianca = PerfilInfantil.objects.create(familia=self.familia, nome='Lu')
        self.rotina = RotinaPlanejada.objects.create(
            familia=self.familia, crianca=self.crianca,
            titulo='Escovar os dentes', criado_por=self.tutor,
        )

    def test_geracao_idempotente_com_uuid(self):
        self.assertIsInstance(self.rotina.pk, uuid.UUID)
        self.assertEqual(self.rotina.gerar_tarefas(timezone.localdate()), 1)
        self.assertEqual(self.rotina.gerar_tarefas(timezone.localdate()), 0)
        tarefa = TarefaAgendada.objects.get(rotina=self.rotina)
        self.assertIsInstance(tarefa.pk, uuid.UUID)

    def test_replicar_na_mesma_familia(self):
        outra = PerfilInfantil.objects.create(familia=self.familia, nome='Leo')
        copia = self.rotina.replicar_rotina(outra)
        self.assertEqual(copia.crianca, outra)
        self.assertNotEqual(copia.pk, self.rotina.pk)
