import uuid
from django.test import TestCase
from .models import Usuario, Familia, PerfilInfantil, ConviteResponsavel


class EsquemaNovoTests(TestCase):
    def test_ids_uuid_e_vinculo_de_tutores(self):
        tutor = Usuario.objects.create_user(username='novo_tutor', password='senha_forte_123')
        familia = Familia.objects.create(nome='Família Nova')
        familia.adicionar_responsavel(tutor)
        crianca = PerfilInfantil.objects.create(familia=familia, nome='Joana')
        self.assertIsInstance(tutor.pk, uuid.UUID)
        self.assertIsInstance(familia.pk, uuid.UUID)
        self.assertIsInstance(crianca.pk, uuid.UUID)
        self.assertTrue(tutor.pode_administrar_familia(familia))
        self.assertEqual(crianca.consultar_saldo(), 0)
        self.assertEqual(crianca.consultar_nivel(), 1)

    def test_nao_remove_ultimo_responsavel(self):
        tutor = Usuario.objects.create_user(username='tutor_unico', password='senha_forte_123')
        familia = Familia.objects.create(nome='Família Única')
        familia.adicionar_responsavel(tutor)
        with self.assertRaises(ValueError):
            familia.remover_responsavel(tutor)
