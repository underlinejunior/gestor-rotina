"""A habilitação do Google não pode desativar o login local."""
from django.test import TestCase, override_settings
from django.urls import reverse
from usuarios.models import Usuario


class AcessoDuploTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="responsavel.duplo", email="exemplo@teste.local",
            password="SenhaForte123", tipo=Usuario.Tipo.TUTOR,
        )

    @override_settings(GOOGLE_OAUTH_ENABLED=True)
    def test_login_por_nome_continua_funcionando(self):
        resposta = self.client.post(reverse("login"), {
            "username": "responsavel.duplo", "password": "SenhaForte123"
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    @override_settings(GOOGLE_OAUTH_ENABLED=True)
    def test_login_por_email(self):
        resposta = self.client.post(reverse("login"), {
            "username": "exemplo@teste.local", "password": "SenhaForte123"
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_conta_google_sem_senha_pode_configurar_login_local(self):
        self.usuario.set_unusable_password()
        self.usuario.save(update_fields=["password"])
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse("configurar_senha_local"), {
            "new_password1": "NovaSenhaLocal123!",
            "new_password2": "NovaSenhaLocal123!",
        })
        self.assertEqual(resposta.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NovaSenhaLocal123!"))
