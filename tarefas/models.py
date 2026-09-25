from datetime import timedelta, time
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from usuarios.models import Familia, PerfilCrianca


def caminho_comprovante(instance, filename):
    agora = timezone.localtime()
    extensao = Path(filename).suffix.lower() or ".jpg"

    return (
        f"comprovantes/{agora:%Y/%m/%d}/"
        f"tarefa_{instance.pk or 'nova'}_"
        f"{agora:%H%M%S%f}{extensao}"
    )


class PeriodoTarefa(models.TextChoices):
    QUALQUER = "QUALQUER", "Qualquer horário"
    MANHA = "MANHA", "🌅 Manhã"
    TARDE = "TARDE", "☀️ Tarde"
    NOITE = "NOITE", "🌙 Noite"
    HORARIO = "HORARIO", "🕐 Horário específico"


class MoldeTarefa(models.Model):
    class Frequencia(models.TextChoices):
        DIARIA = "DIARIA", "Diária"
        SEMANAL = "SEMANAL", "Semanal"

    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name="moldes_tarefas",
    )

    crianca = models.ForeignKey(
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="moldes_tarefas",
    )

    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    pontos_base = models.PositiveSmallIntegerField(default=10)

    frequencia = models.CharField(
        max_length=10,
        choices=Frequencia.choices,
        default=Frequencia.DIARIA,
    )

    dias_semana = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Dias de 0 a 6 separados por vírgula.",
    )

    periodo = models.CharField(
        max_length=12,
        choices=PeriodoTarefa.choices,
        default=PeriodoTarefa.QUALQUER,
        verbose_name="Momento do dia",
    )

    horario = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Horário específico",
    )

    lembrete_ativo = models.BooleanField(
        default=False,
        verbose_name="Lembrar desta tarefa",
    )

    ativa = models.BooleanField(default=True)

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moldes_criados",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("crianca__nome", "titulo")
        verbose_name = "Molde de tarefa"
        verbose_name_plural = "Moldes de tarefas"

    def __str__(self):
        return f"{self.titulo} — {self.crianca.nome_exibicao}"

    @property
    def dias_semana_lista(self):
        if not self.dias_semana:
            return []

        return [
            int(valor)
            for valor in self.dias_semana.split(",")
            if valor.strip().isdigit()
        ]

    @property
    def frequencia_resumo(self):
        if self.frequencia == self.Frequencia.DIARIA:
            return "Todos os dias"

        nomes = {
            0: "Seg",
            1: "Ter",
            2: "Qua",
            3: "Qui",
            4: "Sex",
            5: "Sáb",
            6: "Dom",
        }

        dias = [
            nomes[dia]
            for dia in self.dias_semana_lista
            if dia in nomes
        ]

        return ", ".join(dias) or "Sem dias definidos"

    @property
    def momento_resumo(self):
        if (
            self.periodo == PeriodoTarefa.HORARIO
            and self.horario
        ):
            return self.horario.strftime("%H:%M")

        return self.get_periodo_display()

    @property
    def horario_lembrete(self):
        if not self.lembrete_ativo:
            return None

        if (
            self.periodo == PeriodoTarefa.HORARIO
            and self.horario
        ):
            return self.horario

        return {
            PeriodoTarefa.MANHA: time(8, 0),
            PeriodoTarefa.TARDE: time(15, 0),
            PeriodoTarefa.NOITE: time(19, 0),
        }.get(self.periodo)

    def deve_gerar_em(self, data):
        if not self.ativa:
            return False

        if self.frequencia == self.Frequencia.DIARIA:
            return True

        return data.weekday() in self.dias_semana_lista


class InstanciaTarefa(models.Model):
    class Origem(models.TextChoices):
        MOLDE = "MOLDE", "Molde"
        BONUS = "BONUS", "Bônus"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        REVISAO = "REVISAO", "Aguardando revisão"
        APROVADA = "APROVADA", "Aprovada"
        REJEITADA = "REJEITADA", "Rejeitada"
        NAO_REALIZADA = "NAO_REALIZADA", "Não realizada"

    LIMITE_PROCRASTINACAO_HORAS = 8

    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name="tarefas",
    )

    crianca = models.ForeignKey(
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="tarefas",
    )

    molde = models.ForeignKey(
        MoldeTarefa,
        on_delete=models.SET_NULL,
        related_name="instancias",
        null=True,
        blank=True,
    )

    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tarefas_lancadas",
        null=True,
        blank=True,
    )

    origem = models.CharField(
        max_length=10,
        choices=Origem.choices,
        default=Origem.MOLDE,
    )


    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    pontos_base = models.PositiveSmallIntegerField(default=10)

    periodo = models.CharField(
        max_length=12,
        choices=PeriodoTarefa.choices,
        default=PeriodoTarefa.QUALQUER,
    )

    horario = models.TimeField(
        null=True,
        blank=True,
    )

    lembrete_ativo = models.BooleanField(
        default=False,
    )

    data_referencia = models.DateField(db_index=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        db_index=True,
    )

    foto = models.ImageField(
        upload_to=caminho_comprovante,
        null=True,
        blank=True,
    )

    enviada_em = models.DateTimeField(null=True, blank=True)
    feedback_tutor = models.TextField(blank=True)

    pontos_concedidos = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    revisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tarefas_revisadas",
        null=True,
        blank=True,
    )

    revisada_em = models.DateTimeField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-data_referencia", "status", "criada_em")
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        constraints = [
            models.UniqueConstraint(
                fields=("molde", "data_referencia"),
                condition=Q(molde__isnull=False),
                name="tarefa_unica_por_molde_data",
            )
        ]

    def __str__(self):
        return (
            f"{self.titulo} — "
            f"{self.crianca.nome_exibicao} "
            f"({self.data_referencia:%d/%m/%Y})"
        )

    @property
    def procrastinou(self):
        if not self.enviada_em:
            return False

        limite = self.criada_em + timedelta(
            hours=self.LIMITE_PROCRASTINACAO_HORAS
        )

        return self.enviada_em > limite

    @property
    def momento_resumo(self):
        if (
            self.periodo == PeriodoTarefa.HORARIO
            and self.horario
        ):
            return self.horario.strftime("%H:%M")

        return self.get_periodo_display()

    @property
    def horario_lembrete(self):
        if not self.lembrete_ativo:
            return None

        if (
            self.periodo == PeriodoTarefa.HORARIO
            and self.horario
        ):
            return self.horario

        return {
            PeriodoTarefa.MANHA: time(8, 0),
            PeriodoTarefa.TARDE: time(15, 0),
            PeriodoTarefa.NOITE: time(19, 0),
        }.get(self.periodo)

    @property
    def pode_enviar_comprovante(self):
        return self.status in {
            self.Status.PENDENTE,
            self.Status.REJEITADA,
        }

    @property
    def finalizada(self):
        return self.status in {
            self.Status.APROVADA,
            self.Status.NAO_REALIZADA,
        }


class SugestaoTarefa(models.Model):
    class Categoria(models.TextChoices):
        AUTOCUIDADO = "AUTOCUIDADO", "Autocuidado"
        ORGANIZACAO = "ORGANIZACAO", "Organização"
        ESTUDOS = "ESTUDOS", "Estudos"
        CASA = "CASA", "Casa"
        AUTONOMIA = "AUTONOMIA", "Autonomia"
        COLABORACAO = "COLABORACAO", "Colaboração"

    icone = models.CharField(
        max_length=8,
        default="✨",
    )

    titulo = models.CharField(max_length=120, unique=True)
    descricao = models.TextField(blank=True)

    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
    )

    idade_minima = models.PositiveSmallIntegerField(default=3)
    idade_maxima = models.PositiveSmallIntegerField(default=17)
    pontos_sugeridos = models.PositiveSmallIntegerField(default=5)

    frequencia_sugerida = models.CharField(
        max_length=10,
        choices=MoldeTarefa.Frequencia.choices,
        default=MoldeTarefa.Frequencia.DIARIA,
    )

    dias_semana = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )

    ativa = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("ordem", "titulo")
        verbose_name = "Sugestão de tarefa"
        verbose_name_plural = "Sugestões de tarefas"

    def __str__(self):
        return self.titulo

    @property
    def dias_semana_lista(self):
        if not self.dias_semana:
            return []

        return [
            int(valor)
            for valor in self.dias_semana.split(",")
            if valor.strip().isdigit()
        ]
