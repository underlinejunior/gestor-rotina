import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q

from usuarios.models import PerfilInfantil


class Habilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Intensidade(models.IntegerChoices):
        BAIXA = 1, "Baixa"
        MEDIA = 2, "Média"
        ALTA = 3, "Alta"

    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    icone = models.CharField(max_length=8, default="✨")
    descricao = models.CharField(max_length=220, blank=True)
    ativa = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("ordem", "nome")
        verbose_name = "Habilidade"
        verbose_name_plural = "Habilidades"

    def __str__(self):
        return f"{self.icone} {self.nome}"

    @classmethod
    def calcular_experiencia(cls, intensidade):
        return {
            cls.Intensidade.BAIXA: 3,
            cls.Intensidade.MEDIA: 6,
            cls.Intensidade.ALTA: 10,
        }.get(int(intensidade), 0)

    @classmethod
    def simbolo_intensidade(cls, intensidade):
        return {
            cls.Intensidade.BAIXA: "1",
            cls.Intensidade.MEDIA: "2",
            cls.Intensidade.ALTA: "3",
        }.get(int(intensidade), "")


XP_MAX_HABILIDADE = 250


def dados_nivel_habilidade(xp):
    """
    Escala compacta de evolução das Skills.

    Cada nível ocupa uma faixa de 50 XP e a trilha visual
    é concluída em 250 XP. O XP histórico pode continuar
    acima desse valor, mas a progressão de nível permanece
    no nível 5.
    """
    xp_real = max(0, int(xp or 0))
    xp_considerado = min(xp_real, XP_MAX_HABILIDADE)

    niveis = (
        (1, 0, 50, "Descobrindo"),
        (2, 50, 100, "Praticando"),
        (3, 100, 150, "Evoluindo"),
        (4, 150, 200, "Consolidando"),
        (5, 200, 250, "Dominando"),
    )

    for nivel, inicio, fim, titulo in niveis:
        if xp_considerado < fim:
            intervalo = fim - inicio
            percentual = round(
                ((xp_considerado - inicio) / intervalo) * 100
            )
            percentual = min(100, max(0, percentual))

            return {
                "nivel": nivel,
                "titulo": titulo,
                "inicio": inicio,
                "proximo": fim,
                "percentual": percentual,
                "faltam": max(0, fim - xp_considerado),
                "xp_exibido": xp_considerado,
                "xp_real": xp_real,
                "xp_maximo": XP_MAX_HABILIDADE,
                "concluido": False,
            }

    return {
        "nivel": 5,
        "titulo": "Dominando",
        "inicio": 200,
        "proximo": None,
        "percentual": 100,
        "faltam": 0,
        "xp_exibido": XP_MAX_HABILIDADE,
        "xp_real": xp_real,
        "xp_maximo": XP_MAX_HABILIDADE,
        "concluido": True,
    }


class RotinaHabilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rotina = models.ForeignKey(
        "tarefas.RotinaPlanejada",
        on_delete=models.CASCADE,
        related_name="habilidades_associadas",
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.PROTECT,
        related_name="rotinas_associadas",
    )
    intensidade = models.PositiveSmallIntegerField(
        choices=Habilidade.Intensidade.choices,
        default=Habilidade.Intensidade.MEDIA,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("rotina", "habilidade"),
                name="rotina_habilidade_unica",
            )
        ]

    @property
    def intensidade_simbolo(self):
        return Habilidade.simbolo_intensidade(self.intensidade)


class TarefaHabilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tarefa = models.ForeignKey(
        "tarefas.TarefaAgendada",
        on_delete=models.CASCADE,
        related_name="habilidades_tarefa",
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.PROTECT,
        related_name="instancias_associadas",
    )
    nome_snapshot = models.CharField(max_length=80)
    icone_snapshot = models.CharField(max_length=8, default="✨")
    intensidade = models.PositiveSmallIntegerField(
        choices=Habilidade.Intensidade.choices,
    )
    experiencia_prevista = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tarefa", "habilidade"),
                name="tarefa_habilidade_unica",
            )
        ]

    def calcular_experiencia_prevista(self):
        return Habilidade.calcular_experiencia(self.intensidade)

    @property
    def intensidade_simbolo(self):
        return Habilidade.simbolo_intensidade(self.intensidade)


class SugestaoHabilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sugestao = models.ForeignKey(
        "tarefas.SugestaoAtividade",
        on_delete=models.CASCADE,
        related_name="habilidades_associadas",
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.PROTECT,
        related_name="sugestoes_associadas",
    )
    intensidade = models.PositiveSmallIntegerField(
        choices=Habilidade.Intensidade.choices,
        default=Habilidade.Intensidade.MEDIA,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("sugestao", "habilidade"),
                name="sugestao_habilidade_unica",
            )
        ]


class ProgressoHabilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="progressos_habilidades",
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.PROTECT,
        related_name="progressos",
    )
    experiencia_acumulada = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("crianca", "habilidade"),
                name="progresso_habilidade_crianca_unico",
            )
        ]
        verbose_name = "Progresso de habilidade"
        verbose_name_plural = "Progressos de habilidades"

    def adicionar_experiencia(self, xp, *, tarefa):
        """Credita XP apenas pela tarefa aprovada, com rastreio e idempotência.

        O parâmetro tarefa é obrigatório: não há crédito avulso de XP.
        """
        from tarefas.models import TarefaAgendada
        if tarefa.status != TarefaAgendada.Status.APROVADA or tarefa.crianca_id != self.crianca_id:
            raise ValueError("XP só pode ser concedido por tarefa aprovada da criança.")
        snapshot = tarefa.habilidades_tarefa.filter(habilidade_id=self.habilidade_id).first()
        if snapshot is None or int(xp) != snapshot.experiencia_prevista:
            raise ValueError("XP diferente do previsto para a habilidade desta tarefa.")
        if self.habilidade.slug == "constancia":
            raise ValueError("Constância é medida por dias consecutivos, não por XP.")
        from .services import registrar_xp_habilidades_aprovacao
        registrar_xp_habilidades_aprovacao(tarefa)
        self.refresh_from_db()
        return self.experiencia_acumulada

    def consultar_nivel(self):
        return self.nivel_atual

    def calcular_progresso(self):
        return self.progresso_percentual

    @property
    def dados_nivel(self):
        return dados_nivel_habilidade(self.experiencia_acumulada)

    @property
    def nivel_atual(self):
        return self.dados_nivel["nivel"]

    @property
    def titulo_nivel(self):
        return self.dados_nivel["titulo"]

    @property
    def progresso_percentual(self):
        return self.dados_nivel["percentual"]

    @property
    def xp_para_proximo_nivel(self):
        return self.dados_nivel["faltam"]


class MovimentacaoHabilidade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="movimentos_habilidades",
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.PROTECT,
        related_name="movimentos",
    )
    tarefa = models.ForeignKey(
        "tarefas.TarefaAgendada",
        on_delete=models.SET_NULL,
        related_name="movimentos_habilidades",
        null=True,
        blank=True,
    )
    xp = models.PositiveSmallIntegerField()
    nivel_antes = models.PositiveSmallIntegerField(default=1)
    nivel_depois = models.PositiveSmallIntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em",)
        constraints = [
            models.UniqueConstraint(
                fields=("tarefa", "habilidade"),
                condition=Q(tarefa__isnull=False),
                name="movimentacao_habilidade_tarefa_unica",
            )
        ]
        verbose_name = "Movimento de habilidade"
        verbose_name_plural = "Movimentos de habilidades"

    @property
    def houve_evolucao(self):
        return self.nivel_depois > self.nivel_antes


class MovimentacaoPontos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Tipo(models.TextChoices):
        APROVACAO = "APROVACAO", "Aprovação de tarefa"
        PENALIDADE = "PENALIDADE", "Tarefa não realizada"
        RESGATE = "RESGATE", "Resgate de recompensa"
        AJUSTE = "AJUSTE", "Ajuste manual"

    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="movimentos_pontos",
    )
    tarefa = models.OneToOneField(
        "tarefas.TarefaAgendada",
        on_delete=models.SET_NULL,
        related_name="movimentacao_pontos",
        null=True,
        blank=True,
    )
    # Permite rastrear tanto o débito do resgate quanto sua restituição.
    # Diferentemente de tarefa, um resgate pode ter mais de um movimento.
    resgate = models.ForeignKey(
        "gamificacao.SolicitacaoResgate",
        on_delete=models.SET_NULL,
        related_name="movimentacoes",
        null=True,
        blank=True,
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.APROVACAO,
    )
    pontos = models.IntegerField()
    saldo_resultante = models.IntegerField(default=0)
    nivel_antes = models.PositiveSmallIntegerField(default=1)
    nivel_depois = models.PositiveSmallIntegerField(default=1)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="movimentos_pontos_registrados",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Movimento de pontos"
        verbose_name_plural = "Movimentos de pontos"

    def consultar_pontos(self):
        """Retorna a variação registrada (positiva ou negativa)."""
        return self.pontos

    def consultar_saldo(self):
        """Retorna o saldo após esta movimentação, sem recalcular o histórico."""
        return self.saldo_resultante

    @property
    def houve_evolucao(self):
        return self.nivel_depois > self.nivel_antes


class NotificacaoSistema(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Tipo(models.TextChoices):
        NIVEL_AVATAR = "NIVEL_AVATAR", "Mudança de nível do avatar"
        NIVEL_HABILIDADE = "NIVEL_HABILIDADE", "Mudança de nível de habilidade"
        CONQUISTA = "CONQUISTA", "Conquista desbloqueada"
        RECOMPENSA = "RECOMPENSA", "Recompensa resgatada"
        LEMBRETE_TAREFA = "LEMBRETE_TAREFA", "Lembrete de tarefa"
        TAREFA_NAO_REALIZADA = "TAREFA_NAO_REALIZADA", "Tarefa não realizada"
        RESUMO_DIARIO = "RESUMO_DIARIO", "Resumo diário"
        RESUMO_SEMANAL = "RESUMO_SEMANAL", "Resumo semanal"

    usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes_sistema",
    )
    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    tarefa = models.ForeignKey(
        "tarefas.TarefaAgendada",
        on_delete=models.SET_NULL,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.SET_NULL,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    tipo = models.CharField(
        max_length=30,
        choices=Tipo.choices,
        default=Tipo.NIVEL_AVATAR,
    )
    titulo = models.CharField(max_length=180)
    mensagem = models.TextField(blank=True)
    nivel_anterior = models.PositiveSmallIntegerField(null=True, blank=True)
    nivel_novo = models.PositiveSmallIntegerField(null=True, blank=True)
    url_destino = models.CharField(max_length=255, blank=True, default="")
    chave = models.CharField(
        max_length=180,
        blank=True,
        default="",
        db_index=True,
    )
    visualizada = models.BooleanField(default=False, db_index=True)
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criada_em",)
        verbose_name = "Notificação do sistema"
        verbose_name_plural = "Notificações do sistema"
        constraints = [
            models.UniqueConstraint(
                fields=("usuario_destino", "chave"),
                condition=~Q(chave=""),
                name="notif_chave_usuario_unica",
            )
        ]

    @property
    def icone_bootstrap(self):
        return {
            self.Tipo.NIVEL_AVATAR: "bi-stars",
            self.Tipo.NIVEL_HABILIDADE: "bi-graph-up-arrow",
            self.Tipo.CONQUISTA: "bi-trophy",
            self.Tipo.RECOMPENSA: "bi-gift",
            self.Tipo.LEMBRETE_TAREFA: "bi-alarm",
            self.Tipo.TAREFA_NAO_REALIZADA: "bi-exclamation-circle",
            self.Tipo.RESUMO_DIARIO: "bi-calendar-check",
            self.Tipo.RESUMO_SEMANAL: "bi-bar-chart",
        }.get(self.tipo, "bi-bell")

    @property
    def classe_visual(self):
        return {
            self.Tipo.NIVEL_AVATAR: "notification-level",
            self.Tipo.NIVEL_HABILIDADE: "notification-habilidade",
            self.Tipo.CONQUISTA: "notification-achievement",
            self.Tipo.RECOMPENSA: "notification-reward",
            self.Tipo.LEMBRETE_TAREFA: "notification-reminder",
            self.Tipo.TAREFA_NAO_REALIZADA: "notification-warning",
            self.Tipo.RESUMO_DIARIO: "notification-daily",
            self.Tipo.RESUMO_SEMANAL: "notification-weekly",
        }.get(self.tipo, "notification-default")

    def to_evento(self):
        pill_text = {
            self.Tipo.NIVEL_AVATAR: "🎉 Novo nível desbloqueado",
            self.Tipo.CONQUISTA: "🏆 Nova conquista",
            self.Tipo.RECOMPENSA: "🎁 Novo resgate solicitado",
            self.Tipo.PRIMEIRO_ACESSO if hasattr(self.Tipo, "PRIMEIRO_ACESSO") else "": "✨ Primeiro acesso",
        }.get(self.tipo, "🎉 Destaque especial")

        avatar_emoji = (
            self.crianca.avatar_emoji
            if self.crianca
            else "✨"
        )

        if self.tipo == self.Tipo.CONQUISTA:
            avatar_emoji = "🏆"

        if self.tipo == self.Tipo.RECOMPENSA:
            avatar_emoji = "🎁"

        highlight_text = ""

        if self.tipo == self.Tipo.CONQUISTA:
            if self.usuario_destino.tipo == "CRIANCA":
                highlight_text = (
                    "Você desbloqueou uma nova conquista. "
                    "Continue assim para colecionar medalhas incríveis!"
                )
            else:
                nome = (
                    self.crianca.nome_exibicao
                    if self.crianca
                    else "Uma criança"
                )
                highlight_text = (
                    f"{nome} desbloqueou uma nova conquista. "
                    "Vale comemorar e reforçar esse comportamento!"
                )

        elif self.tipo == self.Tipo.RECOMPENSA:
            nome = (
                self.crianca.nome_exibicao
                if self.crianca
                else "Uma criança"
            )
            highlight_text = (
                f"{nome} acabou de solicitar uma recompensa. "
                "Abra a área de resgates e confirme esse momento especial."
            )

        elif self.tipo == self.Tipo.NIVEL_AVATAR:
            nome = (
                self.crianca.nome_exibicao
                if self.crianca
                else "A criança"
            )
            highlight_text = (
                f"{nome} agora está em destaque como "
                f"{self.crianca.avatar_titulo_nivel if self.crianca else 'novo nível'}."
            )

        return {
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "crianca_nome": (
                self.crianca.nome_exibicao
                if self.crianca
                else ""
            ),
            "avatar_emoji": avatar_emoji,
            "nivel_anterior": self.nivel_anterior,
            "nivel_novo": self.nivel_novo,
            "titulo_novo_nivel": (
                self.crianca.avatar_titulo_nivel
                if self.crianca
                and self.tipo == self.Tipo.NIVEL_AVATAR
                else ""
            ),
            "pill_text": pill_text,
            "highlight_text": highlight_text,
        }


class Recompensa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Categoria(models.TextChoices):
        EXPERIENCIA = "EXPERIENCIA", "❤️ Momento juntos"
        PRIVILEGIO = "PRIVILEGIO", "🎉 Privilégio"
        TEMPO = "TEMPO", "⏱️ Tempo especial"
        OUTRO = "OUTRO", "🎁 Outro"

    familia = models.ForeignKey(
        "usuarios.Familia",
        on_delete=models.CASCADE,
        related_name="recompensas",
    )

    titulo = models.CharField(
        max_length=120,
    )

    descricao = models.TextField(
        blank=True,
    )

    icone = models.CharField(
        max_length=8,
        default="🎁",
    )

    custo_pontos = models.PositiveIntegerField(
        default=50,
    )

    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.EXPERIENCIA,
    )

    ativa = models.BooleanField(
        default=True,
    )

    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recompensas_criadas",
    )

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizada_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = (
            "custo_pontos",
            "titulo",
        )
        verbose_name = "Recompensa"
        verbose_name_plural = "Recompensas"

    def __str__(self):
        return (
            f"{self.icone} {self.titulo} "
            f"({self.custo_pontos} pts)"
        )

    ICONES_CATEGORIA = {
        Categoria.EXPERIENCIA: "❤️",
        Categoria.PRIVILEGIO: "🎉",
        Categoria.TEMPO: "⏱️",
        Categoria.OUTRO: "🎁",
    }

    @classmethod
    def icone_da_categoria(cls, categoria):
        return cls.ICONES_CATEGORIA.get(categoria, "🎁")

    def save(self, *args, **kwargs):
        self.icone = self.icone_da_categoria(self.categoria)
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"icone"}
        return super().save(*args, **kwargs)

    def esta_disponivel(self):
        return self.ativa

    def consultar_custo(self):
        return self.custo_pontos

    def alterar_recompensa(self, *, titulo=None, descricao=None, custo_pontos=None, ativa=None):
        """Altera os dados permitidos sem mudar família ou histórico de resgates."""
        campos = []
        if titulo is not None:
            titulo = titulo.strip()
            if not titulo:
                raise ValueError("O título da recompensa não pode ficar vazio.")
            self.titulo = titulo
            campos.append("titulo")
        if descricao is not None:
            self.descricao = descricao
            campos.append("descricao")
        if custo_pontos is not None:
            custo = int(custo_pontos)
            if custo < 0:
                raise ValueError("O custo não pode ser negativo.")
            self.custo_pontos = custo
            campos.append("custo_pontos")
        if ativa is not None:
            self.ativa = bool(ativa)
            campos.append("ativa")
        if campos:
            self.save(update_fields=campos + ["atualizada_em"])
        return self


class SolicitacaoResgate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ENTREGUE = "ENTREGUE", "Entregue"
        CANCELADO = "CANCELADO", "Cancelado"

    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="resgates_recompensas",
    )

    recompensa = models.ForeignKey(
        Recompensa,
        on_delete=models.SET_NULL,
        related_name="resgates",
        null=True,
        blank=True,
    )

    titulo_snapshot = models.CharField(
        max_length=120,
    )

    icone_snapshot = models.CharField(
        max_length=8,
        default="🎁",
    )

    custo_snapshot = models.PositiveIntegerField()

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.SOLICITADO,
        db_index=True,
    )

    movimentacao_pontos = models.OneToOneField(
        MovimentacaoPontos,
        on_delete=models.SET_NULL,
        related_name="resgate_recompensa",
        null=True,
        blank=True,
    )

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="resgates_registrados",
        help_text="Tutor que registrou a escolha, quando feita de forma assistida.",
    )
    escolha_assistida = models.BooleanField(default=False)

    solicitado_em = models.DateTimeField(
        auto_now_add=True
    )

    concluido_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-solicitado_em",)
        verbose_name = "Resgate de recompensa"
        verbose_name_plural = "Resgates de recompensas"

    def __str__(self):
        return (
            f"{self.crianca.nome_exibicao} — "
            f"{self.titulo_snapshot}"
        )

    @classmethod
    def solicitar_resgate(cls, crianca, recompensa):
        """Usa o serviço transacional que valida família, saldo e débito."""
        from .services import resgatar_recompensa
        return resgatar_recompensa(perfil=crianca, recompensa=recompensa)

    def confirmar_entrega(self, tutor):
        """Não permite confirmar entrega sem autorização do tutor da família."""
        from .services import confirmar_entrega_resgate
        return confirmar_entrega_resgate(resgate=self, tutor=tutor)

    def cancelar_resgate(self, tutor):
        from .services import cancelar_resgate
        return cancelar_resgate(resgate=self, tutor=tutor)


class Conquista(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=80,
        unique=True,
    )

    nome = models.CharField(
        max_length=100,
    )

    descricao = models.CharField(
        max_length=220,
    )

    icone = models.CharField(
        max_length=8,
        default="🏅",
    )

    ordem = models.PositiveSmallIntegerField(
        default=100,
    )

    ativa = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = (
            "ordem",
            "nome",
        )
        verbose_name = "Conquista"
        verbose_name_plural = "Conquistas"

    def __str__(self):
        return f"{self.icone} {self.nome}"


    def verificar_criterio(self, crianca):
        """Verifica as conquistas do perfil pelo serviço central de critérios."""
        if not self.ativa:
            return False
        from .services import avaliar_conquistas
        avaliar_conquistas(crianca)
        return ConquistaInfantil.objects.filter(crianca=crianca, conquista=self).exists()

class ConquistaInfantil(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crianca = models.ForeignKey(
        PerfilInfantil,
        on_delete=models.CASCADE,
        related_name="conquistas_desbloqueadas",
    )

    conquista = models.ForeignKey(
        Conquista,
        on_delete=models.PROTECT,
        related_name="criancas",
    )

    desbloqueada_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = (
            "-desbloqueada_em",
        )
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "crianca",
                    "conquista",
                ),
                name="conquista_crianca_unica",
            )
        ]
        verbose_name = "Conquista da criança"
        verbose_name_plural = "Conquistas das crianças"

    def __str__(self):
        return (
            f"{self.crianca.nome_exibicao} — "
            f"{self.conquista.nome}"
        )

    def consultar_data_desbloqueio(self):
        return self.desbloqueada_em


