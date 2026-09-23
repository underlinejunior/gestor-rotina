from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import PerfilCrianca, Usuario


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for campo in self.fields.values():
            widget = campo.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"

            elif isinstance(widget, forms.RadioSelect):
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


class CadastroTutorForm(
    BootstrapFormMixin,
    UserCreationForm,
):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
    )

    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=False,
    )

    email = forms.EmailField(
        label="E-mail",
        required=True,
    )

    aceite_privacidade = forms.BooleanField(
        label=(
            "Declaro que li a Política de Privacidade e que sou "
            "responsável autorizado pelos dados infantis que cadastrar."
        ),
        required=True,
    )

    class Meta:
        model = Usuario
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if Usuario.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Já existe uma conta cadastrada com este e-mail."
            )

        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.tipo = Usuario.Tipo.TUTOR
        usuario.email = self.cleaned_data["email"]

        if commit:
            usuario.save()

        return usuario


class CriancaForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    usuario_acesso = forms.CharField(
        label="Usuário de acesso",
        max_length=150,
        required=False,
        help_text=(
            "Será usado apenas se a criança tiver acesso "
            "pelo próprio celular."
        ),
    )

    senha = forms.CharField(
        label="Senha",
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = PerfilCrianca
        fields = (
            "nome",
            "data_nascimento",
            "avatar_tipo",
            "acesso_proprio",
        )
        widgets = {
            "data_nascimento": forms.DateInput(
                attrs={"type": "date"}
            ),
            "avatar_tipo": forms.RadioSelect(
                attrs={"class": "avatar-radio"}
            ),
        }
        labels = {
            "nome": "Nome da criança",
            "data_nascimento": "Data de nascimento",
            "avatar_tipo": "Escolha um avatar",
            "acesso_proprio": "Acesso pelo próprio celular",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            self.instance
            and self.instance.pk
            and self.instance.usuario_id
        ):
            self.fields[
                "usuario_acesso"
            ].initial = self.instance.usuario.username

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()

        if not nome:
            raise forms.ValidationError(
                "Informe o nome da criança."
            )

        return nome

    def clean(self):
        dados = super().clean()

        acesso = dados.get("acesso_proprio")
        username = (
            dados.get("usuario_acesso") or ""
        ).strip()

        senha = dados.get("senha")
        confirmar = dados.get("confirmar_senha")

        usuario_atual = None

        if (
            self.instance
            and self.instance.pk
            and self.instance.usuario_id
        ):
            usuario_atual = self.instance.usuario

        if acesso:
            if not username:
                self.add_error(
                    "usuario_acesso",
                    "Informe um usuário para acesso da criança.",
                )
            else:
                consulta = Usuario.objects.filter(
                    username=username
                )

                if usuario_atual:
                    consulta = consulta.exclude(
                        pk=usuario_atual.pk
                    )

                if consulta.exists():
                    self.add_error(
                        "usuario_acesso",
                        "Este usuário já está em uso.",
                    )

            if usuario_atual is None and not senha:
                self.add_error(
                    "senha",
                    "Defina uma senha para o primeiro acesso.",
                )

            if senha and len(senha) < 8:
                self.add_error(
                    "senha",
                    "A senha deve ter pelo menos 8 caracteres.",
                )

            if senha and senha != confirmar:
                self.add_error(
                    "confirmar_senha",
                    "As senhas não coincidem.",
                )

        return dados

    def save(self, familia, commit=True):
        perfil = super().save(commit=False)
        perfil.familia = familia

        acesso = self.cleaned_data["acesso_proprio"]
        username = (
            self.cleaned_data.get("usuario_acesso") or ""
        ).strip()

        senha = self.cleaned_data.get("senha")

        usuario = (
            perfil.usuario
            if perfil.usuario_id
            else None
        )

        if acesso:
            if usuario is None:
                usuario = Usuario(
                    tipo=Usuario.Tipo.CRIANCA
                )

            usuario.username = username
            usuario.first_name = perfil.nome
            usuario.tipo = Usuario.Tipo.CRIANCA
            usuario.is_active = True

            if senha:
                usuario.set_password(senha)

            if commit:
                usuario.save()
                perfil.usuario = usuario

        elif usuario:
            usuario.is_active = False

            if commit:
                usuario.save(
                    update_fields=["is_active"]
                )

        if commit:
            perfil.save()

        return perfil



class CodigoConviteTutorForm(
    BootstrapFormMixin,
    forms.Form,
):
    codigo = forms.CharField(
        label="Código da família",
        max_length=12,
        help_text=(
            "Digite o código compartilhado "
            "por outro responsável."
        ),
    )

    def clean_codigo(self):
        return (
            self.cleaned_data[
                "codigo"
            ]
            .strip()
            .upper()
            .replace(" ", "")
            .replace("-", "")
        )
