from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from tarefas.forms import EnvioComprovanteForm
from tarefas.models import InstanciaTarefa
from usuarios.models import Familia, PerfilCrianca, Usuario


def imagem_jpeg_bytes():
    buffer = BytesIO()
    Image.new("RGB", (32, 32), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


class PrivateEvidenceSecurityTests(TestCase):
    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()

        self.tutor = Usuario.objects.create_user(
            username="tutor_foto",
            password="SenhaSegura123!",
            tipo=Usuario.Tipo.TUTOR,
        )
        self.familia = Familia.objects.create(nome="Família Foto")
        self.familia.tutores.add(self.tutor)

        self.usuario_crianca = Usuario.objects.create_user(
            username="crianca_foto",
            password="SenhaCrianca123!",
            tipo=Usuario.Tipo.CRIANCA,
        )
        self.crianca = PerfilCrianca.objects.create(
            familia=self.familia,
            nome="Criança Foto",
            usuario=self.usuario_crianca,
            acesso_proprio=True,
        )

        self.tarefa = InstanciaTarefa.objects.create(
            familia=self.familia,
            crianca=self.crianca,
            titulo="Guardar brinquedos",
            descricao="",
            pontos_base=10,
            data_referencia=timezone.localdate(),
            status=InstanciaTarefa.Status.REVISAO,
        )
        self.tarefa.foto.save(
            "evidencia.jpg",
            ContentFile(imagem_jpeg_bytes()),
            save=True,
        )

    def tearDown(self):
        # Garante que qualquer FieldFile aberto pelo próprio objeto de teste
        # seja fechado antes de remover o MEDIA_ROOT temporário no Windows.
        try:
            self.tarefa.foto.close()
        except (AttributeError, ValueError):
            pass

        self.media_override.disable()
        self.temp_media.cleanup()

    @staticmethod
    def _consumir_e_fechar_file_response(resposta):
        """Consome o streaming e fecha o arquivo antes do tearDown.

        O Django Test Client mantém FileResponse como resposta de streaming.
        No Windows, o arquivo não pode ser removido pelo TemporaryDirectory
        enquanto o iterator de streaming ainda mantém o handle aberto.
        Consumir o conteúdo dispara o fechamento do wrapper do Test Client;
        o close() no finally deixa a liberação explícita e idempotente.
        """
        try:
            if getattr(resposta, "streaming", False):
                return b"".join(resposta.streaming_content)
            return resposta.content
        finally:
            resposta.close()

    def test_evidencia_exige_autenticacao(self):
        resposta = self.client.get(
            reverse("foto_tarefa_privada", args=[self.tarefa.id])
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("login"), resposta.url)

    def test_tutor_da_familia_acessa_evidencia_sem_cache(self):
        self.client.force_login(self.tutor)
        resposta = self.client.get(
            reverse("foto_tarefa_privada", args=[self.tarefa.id])
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("no-store", resposta["Cache-Control"])
        self.assertEqual(resposta["X-Content-Type-Options"], "nosniff")

        conteudo = self._consumir_e_fechar_file_response(resposta)
        self.assertGreater(len(conteudo), 0)

    def test_crianca_acessa_somente_a_propria_evidencia(self):
        self.client.force_login(self.usuario_crianca)
        resposta = self.client.get(
            reverse("foto_tarefa_privada", args=[self.tarefa.id])
        )
        self.assertEqual(resposta.status_code, 200)

        conteudo = self._consumir_e_fechar_file_response(resposta)
        self.assertGreater(len(conteudo), 0)

    def test_tutor_de_outra_familia_nao_acessa_evidencia(self):
        outro_tutor = Usuario.objects.create_user(
            username="outro_tutor_foto",
            password="SenhaSegura123!",
            tipo=Usuario.Tipo.TUTOR,
        )
        outra_familia = Familia.objects.create(nome="Outra Família")
        outra_familia.tutores.add(outro_tutor)
        self.client.force_login(outro_tutor)

        resposta = self.client.get(
            reverse("foto_tarefa_privada", args=[self.tarefa.id])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_rota_media_publica_nao_entrega_evidencia(self):
        self.client.force_login(self.tutor)
        resposta = self.client.get(f"/media/{self.tarefa.foto.name}")
        self.assertEqual(resposta.status_code, 404)

    def test_retencao_remove_foto_antiga_sem_apagar_historico(self):
        antiga = timezone.now() - timedelta(days=200)
        InstanciaTarefa.objects.filter(pk=self.tarefa.pk).update(
            enviada_em=antiga,
            status=InstanciaTarefa.Status.APROVADA,
        )

        call_command("limpar_evidencias_antigas", dias=180)

        self.tarefa.refresh_from_db()
        self.assertFalse(bool(self.tarefa.foto))
        self.assertEqual(self.tarefa.titulo, "Guardar brinquedos")
        self.assertEqual(self.tarefa.status, InstanciaTarefa.Status.APROVADA)

    def test_formulario_regrava_imagem_em_jpeg_sem_metadados(self):
        arquivo = SimpleUploadedFile(
            "foto-original.jpg",
            imagem_jpeg_bytes(),
            content_type="image/jpeg",
        )
        form = EnvioComprovanteForm(
            files={"foto": arquivo},
        )

        self.assertTrue(form.is_valid(), form.errors)
        foto_limpa = form.cleaned_data["foto"]
        self.assertTrue(foto_limpa.name.endswith(".jpg"))

        with Image.open(foto_limpa) as imagem:
            self.assertEqual(imagem.format, "JPEG")
            self.assertEqual(imagem.getexif(), {})
