"""Filtros combinados por criança e habilidade na listagem familiar."""
from django.test import TestCase
from django.urls import reverse
from gamificacao.models import Habilidade, RotinaHabilidade
from tarefas.models import RotinaPlanejada
from usuarios.models import Familia, PerfilInfantil, Usuario


class FiltragemRotinasTests(TestCase):
    def setUp(self):
        tutor = Usuario.objects.create_user(username="filtro.tutor", password="SenhaForte123")
        familia = Familia.objects.create(nome="Família Filtros")
        familia.tutores.add(tutor)
        self.client.force_login(tutor)
        self.c1 = PerfilInfantil.objects.create(familia=familia, nome="Ana")
        self.c2 = PerfilInfantil.objects.create(familia=familia, nome="Beto")
        self.habilidade, _ = Habilidade.objects.get_or_create(
            slug="foco", defaults={"nome": "Foco", "ativa": True}
        )
        self.r1 = RotinaPlanejada.objects.create(
            familia=familia, crianca=self.c1, criado_por=tutor, titulo="Estudar"
        )
        self.r2 = RotinaPlanejada.objects.create(
            familia=familia, crianca=self.c2, criado_por=tutor, titulo="Guardar brinquedos"
        )
        RotinaHabilidade.objects.create(
            rotina=self.r1, habilidade=self.habilidade, intensidade=1
        )

    def test_filtrar_por_crianca(self):
        resp = self.client.get(reverse("rotinas_listar"), {"crianca": str(self.c1.pk)})
        self.assertEqual(list(resp.context["rotinas"]), [self.r1])

    def test_filtrar_por_habilidade(self):
        resp = self.client.get(reverse("rotinas_listar"), {"habilidade": str(self.habilidade.pk)})
        self.assertEqual(list(resp.context["rotinas"]), [self.r1])

    def test_combinar_filtros_sem_resultados(self):
        resp = self.client.get(reverse("rotinas_listar"), {
            "crianca": str(self.c2.pk), "habilidade": str(self.habilidade.pk)
        })
        self.assertEqual(list(resp.context["rotinas"]), [])
