from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.forms import CriancaForm
from usuarios.models import ConviteTutor, Familia, PerfilCrianca, Usuario


class RF01AutenticacaoEPerfisTests(TestCase):
    """RF01 e RF02 — autenticação e gestão de perfis."""

    def setUp(self):
        self.tutor = Usuario.objects.create_user(
            username="tutor",
            password="SenhaSegura123",
            first_name="Responsável",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Teste")
        self.familia.tutores.add(self.tutor)

    def test_rf01_tutor_autentica_com_usuario_e_senha(self):
        autenticado = self.client.login(
            username="tutor",
            password="SenhaSegura123",
        )

        self.assertTrue(autenticado)

    def test_rf01_crianca_com_acesso_proprio_autentica(self):
        usuario_crianca = Usuario.objects.create_user(
            username="crianca",
            password="SenhaCrianca123",
            first_name="Ana",
            tipo=Usuario.Tipo.CRIANCA,
        )
        PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Ana",
            usuario=usuario_crianca,
            acesso_proprio=True,
        )

        autenticado = self.client.login(
            username="crianca",
            password="SenhaCrianca123",
        )

        self.assertTrue(autenticado)

    def test_rf02_perfil_pode_existir_sem_login_proprio(self):
        perfil = PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Bia",
            acesso_proprio=False,
        )

        self.assertIsNone(perfil.usuario)
        self.assertFalse(perfil.acesso_proprio)
        self.assertEqual(perfil.nome_exibicao, "Bia")

    def test_rf02_formulario_cria_usuario_infantil_quando_acesso_proprio_ativo(self):
        form = CriancaForm(
            data={
                "nome": "Caio",
                "data_nascimento": "2017-05-10",
                "avatar_tipo": PerfilCrianca.AvatarTipo.ROBO,
                "acesso_proprio": "on",
                "usuario_acesso": "caio.rotina",
                "senha": "SenhaCaio123",
                "confirmar_senha": "SenhaCaio123",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        perfil = form.save(familia=self.familia)
        perfil.refresh_from_db()

        self.assertTrue(perfil.acesso_proprio)
        self.assertIsNotNone(perfil.usuario)
        self.assertEqual(perfil.usuario.tipo, Usuario.Tipo.CRIANCA)
        self.assertTrue(perfil.usuario.check_password("SenhaCaio123"))


class RF02FamiliaEPermissoesTests(TestCase):
    """RF02 — vínculo familiar, múltiplos responsáveis e isolamento entre famílias."""

    def setUp(self):
        self.tutor_a = Usuario.objects.create_user(
            username="tutor_a",
            password="Senha12345",
            first_name="Tutor A",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.tutor_b = Usuario.objects.create_user(
            username="tutor_b",
            password="Senha12345",
            first_name="Tutor B",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Principal")
        self.familia.tutores.add(self.tutor_a)

        self.familia_vazia_b = Familia.objects.create(nome="Família de Tutor B")
        self.familia_vazia_b.tutores.add(self.tutor_b)

        self.crianca = PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Criança Teste",
        )

    def test_rf02_convite_permite_segundo_responsavel_na_mesma_familia(self):
        convite = ConviteTutor.objects.create(
            familia=self.familia,
            codigo="123456",
            criado_por=self.tutor_a,
            expira_em=timezone.now() + timedelta(hours=48),
        )

        self.client.force_login(self.tutor_b)
        resposta = self.client.post(
            reverse("familia_entrar_codigo"),
            {"codigo": convite.codigo},
        )

        self.assertRedirects(
            resposta,
            reverse("familia_configuracao"),
        )
        self.assertTrue(
            self.familia.tutores.filter(pk=self.tutor_b.pk).exists()
        )

        convite.refresh_from_db()
        self.assertFalse(convite.ativo)
        self.assertEqual(convite.usado_por, self.tutor_b)
        self.assertIsNotNone(convite.utilizado_em)
        self.assertFalse(
            Familia.objects.filter(pk=self.familia_vazia_b.pk).exists()
        )

    def test_rf02_convite_expirado_nao_pode_ser_usado(self):
        convite = ConviteTutor.objects.create(
            familia=self.familia,
            codigo="654321",
            criado_por=self.tutor_a,
            expira_em=timezone.now() - timedelta(minutes=1),
        )

        self.assertTrue(convite.expirado)
        self.assertFalse(convite.disponivel)

    def test_seguranca_tutor_nao_edita_crianca_de_outra_familia(self):
        outra_familia = Familia.objects.create(nome="Outra Família")
        outro_tutor = Usuario.objects.create_user(
            username="outro_tutor",
            password="Senha12345",
            tipo=Usuario.Tipo.TUTOR,
        )
        outra_familia.tutores.add(outro_tutor)

        self.client.force_login(outro_tutor)
        resposta = self.client.get(
            reverse("crianca_editar", args=[self.crianca.id])
        )

        self.assertEqual(resposta.status_code, 404)


class RNFPWATests(TestCase):
    """RNF01 — comportamento básico do PWA exposto pela aplicação."""

    def test_service_worker_tem_tipo_e_cabecalhos_esperados(self):
        resposta = self.client.get(reverse("service_worker"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta["Content-Type"],
            "application/javascript",
        )
        self.assertEqual(
            resposta["Service-Worker-Allowed"],
            "/",
        )
        self.assertIn("no-store", resposta["Cache-Control"])
