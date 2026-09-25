from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        TUTOR = "TUTOR", "Tutor"
        CRIANCA = "CRIANCA", "Criança"

    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
        default=Tipo.TUTOR,
    )

    boas_vindas_exibidas = models.BooleanField(
        default=False,
        verbose_name="Boas-vindas já exibidas",
    )


    privacidade_aceita_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Política de privacidade aceita em",
    )

    privacidade_versao = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Versão da política de privacidade",
    )

    @property
    def privacidade_pendente(self):
        if self.tipo != self.Tipo.TUTOR:
            return False

        versao_atual = getattr(
            settings,
            "PRIVACY_POLICY_VERSION",
            "",
        )

        return (
            not self.privacidade_aceita_em
            or self.privacidade_versao != versao_atual
        )

    def __str__(self):
        return self.get_full_name() or self.username


class Familia(models.Model):
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da família",
    )

    tutores = models.ManyToManyField(
        Usuario,
        related_name="familias_como_tutor",
        limit_choices_to={"tipo": Usuario.Tipo.TUTOR},
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class PerfilCrianca(models.Model):
    class AvatarTipo(models.TextChoices):
        ROBO = "ROBO", "🤖 Robô"
        RAPOSA = "RAPOSA", "🦊 Raposa"
        DRAGAO = "DRAGAO", "🐲 Dragão"
        ASTRONAUTA = "ASTRONAUTA", "🧑‍🚀 Astronauta"

    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name="criancas",
    )

    nome = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Nome da criança",
    )

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        related_name="perfil_crianca",
        limit_choices_to={"tipo": Usuario.Tipo.CRIANCA},
        null=True,
        blank=True,
    )

    data_nascimento = models.DateField(
        null=True,
        blank=True,
    )

    acesso_proprio = models.BooleanField(
        default=False,
        verbose_name="Acesso pelo próprio celular",
    )

    avatar_tipo = models.CharField(
        max_length=20,
        choices=AvatarTipo.choices,
        default=AvatarTipo.ROBO,
        verbose_name="Avatar",
    )


    saldo_pontos = models.IntegerField(default=0)


    pontos_experiencia = models.PositiveIntegerField(
        default=0,
        verbose_name="XP histórico do avatar",
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil da criança"
        verbose_name_plural = "Perfis das crianças"

    def __str__(self):
        return self.nome_exibicao

    @property
    def nome_exibicao(self):
        if self.nome:
            return self.nome

        if self.usuario:
            return self.usuario.get_full_name() or self.usuario.username

        return f"Criança #{self.pk}"

    @property
    def avatar_emoji(self):
        return {
            self.AvatarTipo.ROBO: "🤖",
            self.AvatarTipo.RAPOSA: "🦊",
            self.AvatarTipo.DRAGAO: "🐲",
            self.AvatarTipo.ASTRONAUTA: "🧑‍🚀",
        }.get(self.avatar_tipo, "🤖")

    @property
    def pontos_evolucao(self):
        """
        Mantém compatibilidade com perfis criados antes do campo
        pontos_experiencia existir. O maior valor histórico conhecido
        é usado como base de evolução.
        """
        return max(
            int(self.pontos_experiencia or 0),
            int(self.saldo_pontos or 0),
            0,
        )

    @property
    def avatar_nivel(self):
        pontos = self.pontos_evolucao

        if pontos >= 500:
            return 5
        if pontos >= 300:
            return 4
        if pontos >= 150:
            return 3
        if pontos >= 50:
            return 2

        return 1

    @property
    def avatar_titulo_nivel(self):
        return {
            1: "Iniciante",
            2: "Explorador",
            3: "Campeão",
            4: "Mestre",
            5: "Lendário",
        }[self.avatar_nivel]

    @property
    def proximo_nivel_pontos(self):
        limites = {
            1: 50,
            2: 150,
            3: 300,
            4: 500,
            5: None,
        }

        return limites[self.avatar_nivel]

    @property
    def pontos_para_proximo_nivel(self):
        proximo = self.proximo_nivel_pontos

        if proximo is None:
            return 0

        return max(
            0,
            proximo - self.pontos_evolucao,
        )

    @property
    def avatar_progresso_percentual(self):
        faixas = {
            1: (0, 50),
            2: (50, 150),
            3: (150, 300),
            4: (300, 500),
            5: (500, 500),
        }

        inicio, fim = faixas[self.avatar_nivel]

        if self.avatar_nivel == 5:
            return 100

        progresso = self.pontos_evolucao - inicio
        intervalo = fim - inicio

        return min(
            100,
            max(
                0,
                round((progresso / intervalo) * 100),
            ),
        )


class ConviteTutor(models.Model):
    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name="convites_tutor",
    )

    codigo = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="convites_tutor_criados",
    )

    usado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="convites_tutor_usados",
        null=True,
        blank=True,
    )

    expira_em = models.DateTimeField()

    ativo = models.BooleanField(
        default=True,
        db_index=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    utilizado_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Convite de responsável"
        verbose_name_plural = "Convites de responsáveis"

    def __str__(self):
        return f"{self.familia} — {self.codigo}"

    @property
    def expirado(self):
        return timezone.now() >= self.expira_em

    @property
    def disponivel(self):
        return (
            self.ativo
            and not self.usado_por_id
            and not self.expirado
        )
