"""Regressões de resgate assistido e apresentação das recompensas."""
from django.test import TestCase
from django.urls import reverse
from gamificacao.models import Recompensa, SolicitacaoResgate, MovimentacaoPontos
from gamificacao.services import resgatar_recompensa
from usuarios.models import Familia, PerfilInfantil, Usuario


class ResgateAssistidoTests(TestCase):
    def setUp(self):
        self.tutor = Usuario.objects.create_user(username="tutor_assist", password="SenhaSegura123")
        self.outro_tutor = Usuario.objects.create_user(username="tutor_externo", password="SenhaSegura123")
        self.familia = Familia.objects.create(nome="Família Teste")
        self.familia.tutores.add(self.tutor)
        outra = Familia.objects.create(nome="Família Externa")
        outra.tutores.add(self.outro_tutor)
        self.crianca = PerfilInfantil.objects.create(
            familia=self.familia, nome="Bebê", acesso_proprio=False, saldo_pontos=100
        )
        self.recompensa = Recompensa.objects.create(
            familia=self.familia, criada_por=self.tutor, titulo="Cinema", custo_pontos=30,
            categoria=Recompensa.Categoria.EXPERIENCIA,
        )

    def test_icone_automatico_da_categoria(self):
        self.assertEqual(self.recompensa.icone, "❤️")
        self.recompensa.categoria = Recompensa.Categoria.TEMPO
        self.recompensa.save(update_fields=["categoria"])
        self.recompensa.refresh_from_db()
        self.assertEqual(self.recompensa.icone, "⏱️")

    def test_resgate_assistido_debita_saldo_e_registra_tutor(self):
        self.client.force_login(self.tutor)
        resposta = self.client.post(
            reverse("recompensa_resgatar", args=[self.recompensa.pk]),
            {"crianca": str(self.crianca.pk)},
        )
        self.assertEqual(resposta.status_code, 302)
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, 70)
        pedido = SolicitacaoResgate.objects.get(crianca=self.crianca)
        self.assertTrue(pedido.escolha_assistida)
        self.assertEqual(pedido.registrado_por, self.tutor)
        self.assertEqual(MovimentacaoPontos.objects.filter(resgate=pedido).count(), 1)

    def test_tutor_de_outra_familia_nao_resgata(self):
        self.client.force_login(self.outro_tutor)
        self.client.post(
            reverse("recompensa_resgatar", args=[self.recompensa.pk]),
            {"crianca": str(self.crianca.pk)},
        )
        self.crianca.refresh_from_db()
        self.assertEqual(self.crianca.saldo_pontos, 100)
        self.assertFalse(SolicitacaoResgate.objects.exists())

    def test_identificador_crianca_invalido_nao_provoca_erro(self):
        self.client.force_login(self.tutor)
        resposta = self.client.post(
            reverse("recompensa_resgatar", args=[self.recompensa.pk]),
            {"crianca": "invalido"},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(SolicitacaoResgate.objects.exists())

    def test_sem_saldo_nao_desconta(self):
        self.crianca.saldo_pontos = 10
        self.crianca.save(update_fields=["saldo_pontos"])
        with self.assertRaises(ValueError):
            resgatar_recompensa(
                perfil=self.crianca, recompensa=self.recompensa, tutor_solicitante=self.tutor
            )
        self.assertEqual(SolicitacaoResgate.objects.count(), 0)

    def test_filtro_categoria(self):
        self.client.force_login(self.tutor)
        resposta = self.client.get(reverse("loja_recompensas"), {"categoria": Recompensa.Categoria.EXPERIENCIA})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["categoria_selecionada"], Recompensa.Categoria.EXPERIENCIA)
        self.assertTrue(all(r.categoria == Recompensa.Categoria.EXPERIENCIA for r in resposta.context["recompensas"]))
