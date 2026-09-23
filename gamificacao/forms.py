from django import forms

from .models import Recompensa


class RecompensaForm(forms.ModelForm):
    class Meta:
        model = Recompensa

        fields = (
            "icone",
            "titulo",
            "descricao",
            "custo_pontos",
            "categoria",
            "ativa",
        )

        labels = {
            "icone": "Ícone",
            "titulo": "Recompensa",
            "descricao": "Descrição",
            "custo_pontos": "Custo em pontos",
            "categoria": "Categoria",
            "ativa": "Disponível na loja",
        }

        widgets = {
            "descricao": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": (
                        "Ex.: escolher o filme da noite "
                        "ou fazer um passeio em família."
                    ),
                }
            ),
            "custo_pontos": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 99999,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(
                widget,
                forms.CheckboxInput,
            ):
                widget.attrs[
                    "class"
                ] = "form-check-input"

            elif isinstance(
                widget,
                forms.Select,
            ):
                widget.attrs[
                    "class"
                ] = "form-select"

            else:
                widget.attrs[
                    "class"
                ] = "form-control"

        self.fields["icone"].widget.attrs.update(
            {
                "maxlength": 8,
                "placeholder": "🎁",
            }
        )
