from django.conf import settings
from django.db import models
from django.db.models import Q

from usuarios.models import PerfilCrianca


class Skill(models.Model):
    class Impacto(models.IntegerChoices):
        LEVE = 1, "Leve"
        MEDIO = 2, "Médio"
        FORTE = 3, "Forte"

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
    def xp_por_impacto(cls, impacto):
        return {
            cls.Impacto.LEVE: 3,
            cls.Impacto.MEDIO: 6,
            cls.Impacto.FORTE: 10,
        }.get(int(impacto), 0)

    @classmethod
    def simbolo_impacto(cls, impacto):
        return {
            cls.Impacto.LEVE: "+",
            cls.Impacto.MEDIO: "++",
            cls.Impacto.FORTE: "+++",
        }.get(int(impacto), "")


def dados_nivel_skill(xp):
    xp = max(0, int(xp or 0))
    niveis = (
        (1, 0, 60, "Descobrindo"),
        (2, 60, 150, "Praticando"),
        (3, 150, 300, "Evoluindo"),
        (4, 300, 500, "Consolidando"),
        (5, 500, None, "Dominando"),
    )

    for nivel, inicio, fim, titulo in niveis:
        if fim is None or xp < fim:
            if fim is None:
                percentual = 100
                faltam = 0
            else:
                intervalo = fim - inicio
                percentual = round(
                    ((xp - inicio) / intervalo) * 100
                )
                percentual = min(100, max(0, percentual))
                faltam = max(0, fim - xp)

            return {
                "nivel": nivel,
                "titulo": titulo,
                "inicio": inicio,
                "proximo": fim,
                "percentual": percentual,
                "faltam": faltam,
            }

    return {
        "nivel": 5,
        "titulo": "Dominando",
        "inicio": 500,
        "proximo": None,
        "percentual": 100,
        "faltam": 0,
    }


class MoldeTarefaSkill(models.Model):
    molde = models.ForeignKey(
        "tarefas.MoldeTarefa",
        on_delete=models.CASCADE,
        related_name="skills_associadas",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="moldes_associados",
    )
    impacto = models.PositiveSmallIntegerField(
        choices=Skill.Impacto.choices,
        default=Skill.Impacto.MEDIO,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("molde", "skill"),
                name="molde_skill_unica",
            )
        ]

    @property
    def impacto_simbolo(self):
        return Skill.simbolo_impacto(self.impacto)


class InstanciaTarefaSkill(models.Model):
    tarefa = models.ForeignKey(
        "tarefas.InstanciaTarefa",
        on_delete=models.CASCADE,
        related_name="skills_snapshot",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="instancias_associadas",
    )
    nome_snapshot = models.CharField(max_length=80)
    icone_snapshot = models.CharField(max_length=8, default="✨")
    impacto = models.PositiveSmallIntegerField(
        choices=Skill.Impacto.choices,
    )
    xp_planejado = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tarefa", "skill"),
                name="instancia_skill_unica",
            )
        ]

    @property
    def impacto_simbolo(self):
        return Skill.simbolo_impacto(self.impacto)


class SugestaoTarefaSkill(models.Model):
    sugestao = models.ForeignKey(
        "tarefas.SugestaoTarefa",
        on_delete=models.CASCADE,
        related_name="skills_associadas",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="sugestoes_associadas",
    )
    impacto = models.PositiveSmallIntegerField(
        choices=Skill.Impacto.choices,
        default=Skill.Impacto.MEDIO,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("sugestao", "skill"),
                name="sugestao_skill_unica",
            )
        ]


class ProgressoSkill(models.Model):
    crianca = models.ForeignKey(
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="progressos_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="progressos",
    )
    xp_total = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("crianca", "skill"),
                name="progresso_skill_crianca_unico",
            )
        ]
        verbose_name = "Progresso de habilidade"
        verbose_name_plural = "Progressos de habilidades"

    @property
    def dados_nivel(self):
        return dados_nivel_skill(self.xp_total)

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


class MovimentoSkill(models.Model):
    crianca = models.ForeignKey(
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="movimentos_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="movimentos",
    )
    tarefa = models.ForeignKey(
        "tarefas.InstanciaTarefa",
        on_delete=models.SET_NULL,
        related_name="movimentos_skills",
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
                fields=("tarefa", "skill"),
                condition=Q(tarefa__isnull=False),
                name="movimento_skill_tarefa_unico",
            )
        ]
        verbose_name = "Movimento de habilidade"
        verbose_name_plural = "Movimentos de habilidades"

    @property
    def houve_evolucao(self):
        return self.nivel_depois > self.nivel_antes


class MovimentoPontos(models.Model):
    class Tipo(models.TextChoices):
        APROVACAO = "APROVACAO", "Aprovação de tarefa"
        PENALIDADE = "PENALIDADE", "Tarefa não realizada"
        RESGATE = "RESGATE", "Resgate de recompensa"
        AJUSTE = "AJUSTE", "Ajuste manual"

    crianca = models.ForeignKey(
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="movimentos_pontos",
    )
    tarefa = models.OneToOneField(
        "tarefas.InstanciaTarefa",
        on_delete=models.SET_NULL,
        related_name="movimento_pontos",
        null=True,
        blank=True,
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.APROVACAO,
    )
    pontos = models.IntegerField()
    saldo_apos = models.IntegerField(default=0)
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

    @property
    def houve_evolucao(self):
        return self.nivel_depois > self.nivel_antes


class NotificacaoSistema(models.Model):
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
        PerfilCrianca,
        on_delete=models.CASCADE,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    tarefa = models.ForeignKey(
        "tarefas.InstanciaTarefa",
        on_delete=models.SET_NULL,
        related_name="notificacoes_sistema",
        null=True,
        blank=True,
    )
    skill = models.ForeignKey(
        Skill,
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
            self.Tipo.NIVEL_HABILIDADE: "notification-skill",
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


class ResgateRecompensa(models.Model):
    class Status(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ENTREGUE = "ENTREGUE", "Entregue"
        CANCELADO = "CANCELADO", "Cancelado"

    crianca = models.ForeignKey(
        PerfilCrianca,
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

    movimento_pontos = models.OneToOneField(
        MovimentoPontos,
        on_delete=models.SET_NULL,
        related_name="resgate_recompensa",
        null=True,
        blank=True,
    )

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


class Conquista(models.Model):
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


class ConquistaCrianca(models.Model):
    crianca = models.ForeignKey(
        PerfilCrianca,
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
