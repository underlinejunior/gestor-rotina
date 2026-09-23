from io import BytesIO
from pathlib import Path

from django import forms
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from gamificacao.models import Skill
from usuarios.models import PerfilCrianca

from .models import MoldeTarefa, PeriodoTarefa


DIAS_SEMANA = (
    ("0", "Seg"),
    ("1", "Ter"),
    ("2", "Qua"),
    ("3", "Qui"),
    ("4", "Sex"),
    ("5", "Sáb"),
    ("6", "Dom"),
)


class BootstrapFormMixin:
    def aplicar_bootstrap(self):
        for campo in self.fields.values():
            widget = campo.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"

            elif isinstance(widget, forms.CheckboxSelectMultiple):
                continue

            elif isinstance(
                widget,
                (forms.Select, forms.SelectMultiple),
            ):
                widget.attrs["class"] = "form-select"

            else:
                classe_atual = widget.attrs.get("class", "")
                widget.attrs["class"] = (
                    f"{classe_atual} form-control"
                ).strip()


class SkillImpactMixin:
    def obter_impactos_skills(self):
        impactos = {}

        for skill in Skill.objects.filter(
            ativa=True
        ):
            chave = (
                f"skill_impact_"
                f"{skill.id}"
            )

            valor = (
                self.data.get(chave)
                if self.is_bound
                else None
            )

            try:
                valor = int(
                    valor or 0
                )
            except (TypeError, ValueError):
                valor = 0

            if valor in {
                Skill.Impacto.LEVE,
                Skill.Impacto.MEDIO,
                Skill.Impacto.FORTE,
            }:
                impactos[
                    skill.id
                ] = valor

        return impactos


class MoldeTarefaForm(
    SkillImpactMixin,
    BootstrapFormMixin,
    forms.ModelForm,
):
    dias_semana_selecionados = forms.MultipleChoiceField(
        label="Dias da semana",
        choices=DIAS_SEMANA,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    replicar_todas = forms.BooleanField(
        label="Replicar para todas as crianças",
        required=False,
        help_text=(
            "Cria esta mesma rotina para todas as crianças "
            "da família. A criança selecionada acima continua "
            "sendo usada como referência para as sugestões."
        ),
    )

    class Meta:
        model = MoldeTarefa
        fields = (
            "crianca",
            "titulo",
            "descricao",
            "pontos_base",
            "frequencia",
            "periodo",
            "horario",
            "lembrete_ativo",
            "ativa",
        )
        labels = {
            "crianca": "Criança",
            "titulo": "Tarefa",
            "descricao": "Descrição",
            "pontos_base": "Pontos",
            "frequencia": "Frequência",
            "periodo": "Momento do dia",
            "horario": "Horário",
            "lembrete_ativo": "Lembrar desta tarefa",
            "ativa": "Rotina ativa",
        }
        widgets = {
            "descricao": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": (
                        "Explique de forma simples "
                        "o que deve ser feito."
                    ),
                }
            ),
            "pontos_base": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 999,
                }
            ),
            "horario": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
        }

    def __init__(
        self,
        *args,
        familia=None,
        permitir_replicacao=True,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.aplicar_bootstrap()

        if not permitir_replicacao:
            self.fields.pop(
                "replicar_todas",
                None,
            )

        if familia is not None:
            self.fields[
                "crianca"
            ].queryset = (
                PerfilCrianca.objects
                .filter(familia=familia)
                .order_by("nome")
            )

        if (
            self.instance
            and self.instance.pk
            and self.instance.dias_semana
        ):
            self.fields[
                "dias_semana_selecionados"
            ].initial = [
                str(valor)
                for valor in (
                    self.instance
                    .dias_semana_lista
                )
            ]

    def clean(self):
        dados = super().clean()

        frequencia = dados.get(
            "frequencia"
        )

        dias = dados.get(
            "dias_semana_selecionados"
        )

        if (
            frequencia
            == MoldeTarefa.Frequencia.SEMANAL
            and not dias
        ):
            self.add_error(
                "dias_semana_selecionados",
                (
                    "Escolha pelo menos "
                    "um dia para a rotina semanal."
                ),
            )

        periodo = dados.get(
            "periodo"
        )

        horario = dados.get(
            "horario"
        )

        if (
            periodo
            == PeriodoTarefa.HORARIO
            and not horario
        ):
            self.add_error(
                "horario",
                (
                    "Informe o horário "
                    "específico da tarefa."
                ),
            )

        if (
            periodo
            != PeriodoTarefa.HORARIO
        ):
            dados["horario"] = None

        if (
            dados.get("lembrete_ativo")
            and periodo
            == PeriodoTarefa.QUALQUER
        ):
            self.add_error(
                "periodo",
                (
                    "Escolha manhã, tarde, noite "
                    "ou um horário específico "
                    "para ativar o lembrete."
                ),
            )

        return dados

    def save(self, commit=True):
        molde = super().save(
            commit=False
        )

        if (
            molde.frequencia
            == MoldeTarefa.Frequencia.SEMANAL
        ):
            dias = self.cleaned_data.get(
                "dias_semana_selecionados",
                [],
            )
            molde.dias_semana = ",".join(
                sorted(dias)
            )
        else:
            molde.dias_semana = ""

        if commit:
            molde.save()

        return molde


class TarefaBonusForm(
    SkillImpactMixin,
    BootstrapFormMixin,
    forms.Form,
):
    crianca = forms.ModelChoiceField(
        label="Criança",
        queryset=PerfilCrianca.objects.none(),
    )
    titulo = forms.CharField(
        label="Tarefa",
        max_length=120,
    )
    descricao = forms.CharField(
        label="Descrição",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3}
        ),
    )
    pontos_base = forms.IntegerField(
        label="Pontos",
        min_value=1,
        max_value=999,
        initial=10,
    )

    def __init__(
        self,
        *args,
        familia=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.aplicar_bootstrap()

        if familia is not None:
            self.fields[
                "crianca"
            ].queryset = (
                PerfilCrianca.objects
                .filter(familia=familia)
                .order_by("nome")
            )


class EnvioComprovanteForm(forms.Form):
    foto = forms.ImageField(
        label="Foto da tarefa concluída",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/*",
                "capture": "environment",
                "class": "camera-input",
            }
        ),
    )

    def clean_foto(self):
        foto = self.cleaned_data["foto"]

        limite = 8 * 1024 * 1024

        if foto.size > limite:
            raise forms.ValidationError(
                "A imagem deve ter no máximo 8 MB."
            )

        try:
            foto.seek(0)
            imagem = Image.open(foto)
            imagem.load()
        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError(
                "Envie um arquivo de imagem válido."
            )

        if imagem.width * imagem.height > 20_000_000:
            raise forms.ValidationError(
                "A resolução da imagem é muito alta."
            )

        # Corrige orientação e regrava a imagem sem EXIF/GPS. Além de reduzir
        # metadados pessoais desnecessários, limita o tamanho armazenado.
        imagem = ImageOps.exif_transpose(imagem)
        imagem.thumbnail((1920, 1920))

        if "A" in imagem.getbands():
            fundo = Image.new(
                "RGB",
                imagem.size,
                "white",
            )
            fundo.paste(
                imagem,
                mask=imagem.getchannel("A"),
            )
            imagem = fundo
        elif imagem.mode != "RGB":
            imagem = imagem.convert("RGB")

        buffer = BytesIO()
        imagem.save(
            buffer,
            format="JPEG",
            quality=85,
            optimize=True,
        )

        nome = f"{Path(foto.name).stem or 'evidencia'}.jpg"

        return ContentFile(
            buffer.getvalue(),
            name=nome,
        )


class RevisaoTarefaForm(
    BootstrapFormMixin,
    forms.Form,
):
    pontos_concedidos = forms.IntegerField(
        label="Pontuação final",
        min_value=0,
        max_value=999,
        required=False,
    )

    feedback_tutor = forms.CharField(
        label="Feedback",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Escreva um elogio, "
                    "orientação ou o motivo "
                    "da rejeição."
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        pontos_iniciais=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.aplicar_bootstrap()

        if (
            not self.is_bound
            and pontos_iniciais is not None
        ):
            self.fields[
                "pontos_concedidos"
            ].initial = pontos_iniciais
