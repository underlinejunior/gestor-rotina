"""Cobertura complementar dos requisitos RF21A/B/C de privacidade do RTS."""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from usuarios.forms import CadastroTutorForm
from usuarios.models import Familia, PerfilInfantil, Usuario


class PrivacidadeRastreabilidadeTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(
            username="tutor_priv_audit", password="SenhaSegura2026!",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Privada")
        self.familia.tutores.add(self.tutor)
        self.crianca = PerfilInfantil.objects.create(familia=self.familia, nome="Criança Privada")

    def test_rf21a_cadastro_nao_aceita_sem_ciencia_da_politica(self):
        form = CadastroTutorForm(data={
            "username": "novo_responsavel", "first_name": "Novo",
            "email": "novo@example.com", "password1": "SenhaSegura2026!",
            "password2": "SenhaSegura2026!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("aceite_privacidade", form.errors)

    @override_settings(PRIVACY_POLICY_VERSION="2026.2")
    def test_rf21a_aceite_registra_data_e_versao(self):
        self.client.force_login(self.tutor)
        resposta = self.client.post(reverse("privacidade_aceite"), {"aceite": "on"})
        self.assertEqual(resposta.status_code, 302)
        self.tutor.refresh_from_db()
        self.assertIsNotNone(self.tutor.privacidade_aceita_em)
        self.assertEqual(self.tutor.privacidade_versao, "2026.2")

    def test_rf21b_exportacao_privada_e_sem_cache(self):
        self.client.force_login(self.tutor)
        resposta = self.client.get(reverse("privacidade_exportar"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("no-store", resposta["Cache-Control"])
        dados = resposta.json()
        self.assertEqual(dados["familia"]["nome"], self.familia.nome)
        self.assertEqual(len(dados["criancas"]), 1)
        self.assertEqual(dados["criancas"][0]["nome"], "Criança Privada")
        estranho = Usuario.objects.create_user(username="tutor_priv_estranho", password="SenhaSegura2026!")
        outra = Familia.objects.create(nome="Família Estranha")
        outra.tutores.add(estranho)
        PerfilInfantil.objects.create(familia=outra, nome="Dado confidencial")
        resposta = self.client.get(reverse("privacidade_exportar"))
        self.assertNotIn("Dado confidencial", str(resposta.content))

    def test_rf21c_exclusao_exige_post_e_confirmacao(self):
        self.client.force_login(self.tutor)
        self.assertEqual(self.client.get(reverse("privacidade_excluir_conta")).status_code, 405)
        self.client.post(reverse("privacidade_excluir_conta"), {"confirmacao": "INDEVIDA"})
        self.assertTrue(Usuario.objects.filter(pk=self.tutor.pk).exists())
        self.assertTrue(Familia.objects.filter(pk=self.familia.pk).exists())

    def test_rf21c_exclusao_de_tutor_unico_remove_familia(self):
        self.client.force_login(self.tutor)
        resposta = self.client.post(reverse("privacidade_excluir_conta"), {"confirmacao": "EXCLUIR"})
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Usuario.objects.filter(pk=self.tutor.pk).exists())
        self.assertFalse(Familia.objects.filter(pk=self.familia.pk).exists())
