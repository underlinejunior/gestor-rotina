"""Métodos do diagrama de acesso e família."""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from .models import Usuario, Familia, ConviteResponsavel


class DiagramaConvitesTests(TestCase):
    def test_utilizar_convite_por_tutor_vinculado(self):
        criador = Usuario.objects.create_user(username="uml_criador", password="uma_senha_forte")
        novo = Usuario.objects.create_user(username="uml_novo", password="uma_senha_forte")
        familia = Familia.objects.create(nome="Família dos testes")
        familia.adicionar_responsavel(criador)
        convite = ConviteResponsavel.objects.create(
            familia=familia, codigo="UMLCONVITE1", criado_por=criador,
            expira_em=timezone.now() + timedelta(days=1))
        with self.assertRaises(ValueError):
            convite.utilizar(novo)
        familia.adicionar_responsavel(novo)
        convite.utilizar(novo)
        self.assertFalse(convite.esta_disponivel())
        self.assertEqual(convite.usado_por, novo)
        with self.assertRaises(ValueError):
            convite.utilizar(novo)

class NomeRealPerfilInfantilTests(TestCase):
    def test_classe_registrada_corresponde_ao_diagrama(self):
        from django.apps import apps
        from .models import PerfilInfantil
        self.assertIs(apps.get_model("usuarios", "PerfilInfantil"), PerfilInfantil)
