import json
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from usuarios.forms import CadastroTutorForm
from usuarios.models import Familia, PerfilCrianca, Usuario


class PrivacyAndAccountSecurityTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(
            username="tutor_privacidade",
            password="SenhaSegura123!",
            tipo=Usuario.Tipo.TUTOR,
            email="tutor@example.com",
        )
        self.familia = Familia.objects.create(nome="Família Privacidade")
        self.familia.tutores.add(self.tutor)

    def test_cadastro_exige_ciencia_da_politica(self):
        dados = {
            "first_name": "Novo",
            "last_name": "Tutor",
            "email": "novo@example.com",
            "username": "novo_tutor",
            "password1": "UmaSenhaForte123!",
            "password2": "UmaSenhaForte123!",
        }

        form = CadastroTutorForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn("aceite_privacidade", form.errors)

        dados["aceite_privacidade"] = True
        form = CadastroTutorForm(data=dados)
        self.assertTrue(form.is_valid(), form.errors)

    def test_aceite_registra_data_e_versao_vigente(self):
        self.client.force_login(self.tutor)

        resposta = self.client.post(
            reverse("privacidade_aceite"),
            {"aceite": "on"},
        )

        self.assertRedirects(resposta, reverse("inicio"))
        self.tutor.refresh_from_db()
        self.assertIsNotNone(self.tutor.privacidade_aceita_em)
        self.assertEqual(
            self.tutor.privacidade_versao,
            settings.PRIVACY_POLICY_VERSION,
        )

    def test_exportacao_e_privada_e_sem_cache(self):
        PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Criança Teste",
        )
        self.client.force_login(self.tutor)

        resposta = self.client.get(reverse("privacidade_exportar"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Cache-Control"], "private, no-store")
        self.assertIn("attachment;", resposta["Content-Disposition"])

        dados = json.loads(resposta.content.decode("utf-8"))
        self.assertEqual(dados["familia"]["id"], self.familia.id)
        self.assertEqual(len(dados["criancas"]), 1)

    def test_logout_exige_post(self):
        self.client.force_login(self.tutor)

        resposta_get = self.client.get(reverse("logout"))
        self.assertEqual(resposta_get.status_code, 405)

        resposta_post = self.client.post(reverse("logout"))
        self.assertRedirects(resposta_post, reverse("login"))

    def test_operacao_sensivel_sem_csrf_e_rejeitada(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.tutor)

        resposta = client.post(reverse("privacidade_apagar_evidencias"))
        self.assertEqual(resposta.status_code, 403)

    def test_exclusao_do_unico_tutor_remove_familia_e_conta(self):
        usuario_id = self.tutor.id
        familia_id = self.familia.id
        self.client.force_login(self.tutor)

        resposta = self.client.post(
            reverse("privacidade_excluir_conta"),
            {"confirmacao": "EXCLUIR"},
        )

        self.assertRedirects(resposta, reverse("login"))
        self.assertFalse(Usuario.objects.filter(pk=usuario_id).exists())
        self.assertFalse(Familia.objects.filter(pk=familia_id).exists())

    def test_exclusao_em_familia_compartilhada_anonimiza_tutor(self):
        outro_tutor = Usuario.objects.create_user(
            username="outro_responsavel",
            password="SenhaSegura123!",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia.tutores.add(outro_tutor)
        usuario_id = self.tutor.id
        self.client.force_login(self.tutor)

        resposta = self.client.post(
            reverse("privacidade_excluir_conta"),
            {"confirmacao": "EXCLUIR"},
        )

        self.assertRedirects(resposta, reverse("login"))
        usuario = Usuario.objects.get(pk=usuario_id)
        self.assertFalse(usuario.is_active)
        self.assertEqual(usuario.email, "")
        self.assertFalse(self.familia.tutores.filter(pk=usuario_id).exists())
        self.assertTrue(self.familia.tutores.filter(pk=outro_tutor.pk).exists())

    def test_crianca_nao_acessa_central_de_privacidade_do_tutor(self):
        usuario_crianca = Usuario.objects.create_user(
            username="crianca_privacidade",
            password="SenhaCrianca123!",
            tipo=Usuario.Tipo.CRIANCA,
        )
        PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Criança",
            usuario=usuario_crianca,
            acesso_proprio=True,
        )
        self.client.force_login(usuario_crianca)

        resposta = self.client.get(reverse("privacidade_central"))
        self.assertRedirects(resposta, reverse("inicio"))
