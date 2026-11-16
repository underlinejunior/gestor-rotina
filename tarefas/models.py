import uuid
from datetime import timedelta, time
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from usuarios.models import Familia, PerfilInfantil


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


class RotinaPlanejada(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Frequencia(models.TextChoices):
        DIARIA = "DIARIA", "Diária"
        SEMANAL = "SEMANAL", "Semanal"

    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name="rotinas_planejadas",
    )

    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="rotinas_planejadas",
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

    sugestao_origem = models.ForeignKey(
        "tarefas.SugestaoAtividade",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="rotinas_criadas",
        help_text="Sugestão de catálogo escolhida, quando aplicável.",
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rotinas_criadas",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("crianca__nome", "titulo")
        verbose_name = "Rotina planejada"
        verbose_name_plural = "Rotinas planejadas"

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

    def alterar_planejamento(self, **alteracoes):
        """Atualiza somente campos editáveis, preservando tarefas já geradas."""
        permitidos = {
            "titulo", "descricao", "pontos_base", "frequencia",
            "dias_semana", "periodo", "horario", "lembrete_ativo", "ativa",
        }
        invalidos = set(alteracoes) - permitidos
        if invalidos:
            raise ValueError("Campos não permitidos: " + ", ".join(sorted(invalidos)))
        for campo, valor in alteracoes.items():
            setattr(self, campo, valor)
        self.full_clean()
        if alteracoes:
            self.save(update_fields=[*alteracoes.keys(), "atualizado_em"])
        return self

    def ativar(self):
        """Reativa a rotina sem modificar tarefas históricas."""
        if not self.ativa:
            self.ativa = True
            self.save(update_fields=("ativa", "atualizado_em"))

    def desativar(self):
        """Suspende novas gerações; registros anteriores são preservados."""
        if self.ativa:
            self.ativa = False
            self.save(update_fields=("ativa", "atualizado_em"))

    def gerar_tarefas(self, data=None):
        """Aciona o serviço de geração; a restrição de unicidade evita duplicações."""
        from .services import gerar_tarefas_do_dia
        return gerar_tarefas_do_dia(familia=self.familia, data=data, rotina=self)

    def obter_horario_lembrete(self):
        return self.horario_lembrete

    def replicar_rotina(self, crianca):
        """Copia a rotina e suas habilidades para outra criança da mesma família."""
        if crianca.familia_id != self.familia_id:
            raise ValueError("Não é permitido replicar entre famílias diferentes.")
        from django.db import transaction
        from gamificacao.models import RotinaHabilidade
        with transaction.atomic():
            copia = RotinaPlanejada.objects.create(
                familia=self.familia,
                crianca=crianca,
                titulo=self.titulo,
                descricao=self.descricao,
                pontos_base=self.pontos_base,
                frequencia=self.frequencia,
                dias_semana=self.dias_semana,
                periodo=self.periodo,
                horario=self.horario,
                lembrete_ativo=self.lembrete_ativo,
                ativa=self.ativa,
                criado_por=self.criado_por,
                sugestao_origem=self.sugestao_origem,
            )
            RotinaHabilidade.objects.bulk_create([
                RotinaHabilidade(
                    rotina=copia,
                    habilidade=associacao.habilidade,
                    intensidade=associacao.intensidade,
                )
                for associacao in self.habilidades_associadas.all()
            ])
        return copia

    def deve_gerar_em(self, data):
        if not self.ativa:
            return False

        if self.frequencia == self.Frequencia.DIARIA:
            return True

        return data.weekday() in self.dias_semana_lista


class TarefaAgendada(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Origem(models.TextChoices):
        ROTINA = "ROTINA", "Rotina planejada"
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
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="tarefas",
    )

    rotina = models.ForeignKey(
        RotinaPlanejada,
        on_delete=models.SET_NULL,
        related_name="tarefas_agendadas",
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
        default=Origem.ROTINA,
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
                fields=("rotina", "data_referencia"),
                condition=Q(rotina__isnull=False),
                name="tarefa_unica_por_rotina_data",
            )
        ]

    def __str__(self):
        return (
            f"{self.titulo} — "
            f"{self.crianca.nome_exibicao} "
            f"({self.data_referencia:%d/%m/%Y})"
        )

    @classmethod
    def criar_tarefa_bonus(cls, *, tutor, crianca, titulo, descricao="", pontos_base=10, data=None):
        from usuarios.models import Usuario
        if (not getattr(tutor, "is_authenticated", False)
                or tutor.tipo != Usuario.Tipo.TUTOR
                or not crianca.familia.tutores.filter(pk=tutor.pk).exists()):
            raise ValueError("Somente tutor da família pode criar bônus.")
        return cls.objects.create(
            familia=crianca.familia, crianca=crianca, criada_por=tutor,
            origem=cls.Origem.BONUS, titulo=titulo, descricao=descricao,
            pontos_base=pontos_base, data_referencia=data or timezone.localdate(),
        )

    def marcar_nao_realizada(self, hoje=None):
        """Delega o encerramento ao serviço, com débito e auditoria únicos."""
        from .services import encerrar_tarefas_antigas
        hoje = hoje or timezone.localdate()
        if self.data_referencia >= hoje:
            raise ValueError("A tarefa ainda não venceu.")
        if self.status not in {self.Status.PENDENTE, self.Status.REJEITADA}:
            raise ValueError("A tarefa não pode ser encerrada neste estado.")
        # O serviço centralizado processa tarefas vencidas; nunca altera só o status.
        encerrar_tarefas_antigas(familia=self.familia, hoje=hoje, tarefa=self)
        self.refresh_from_db()
        return self.status == self.Status.NAO_REALIZADA

    def registrar_evidencia(self, foto):
        from .services import enviar_comprovante
        return enviar_comprovante(self, foto)

    def aprovar(self, tutor, pontos=None, feedback=""):
        from .services import aprovar_tarefa
        return aprovar_tarefa(self, tutor, self.pontos_base if pontos is None else pontos, feedback)

    def rejeitar(self, tutor, feedback=""):
        from .services import rejeitar_tarefa
        return rejeitar_tarefa(self, tutor, feedback)

    def esta_finalizada(self):
        return self.finalizada

    def identificar_atraso(self):
        return self.procrastinou

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


class SugestaoAtividade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        choices=RotinaPlanejada.Frequencia.choices,
        default=RotinaPlanejada.Frequencia.DIARIA,
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

    def adequada_para_idade(self, idade):
        return self.ativa and self.idade_minima <= idade <= self.idade_maxima

    def esta_disponivel(self):
        return self.ativa

    @property
    def dias_semana_lista(self):
        if not self.dias_semana:
            return []

        return [
            int(valor)
            for valor in self.dias_semana.split(",")
            if valor.strip().isdigit()
        ]


