from allauth.socialaccount.adapter import (
    DefaultSocialAccountAdapter,
)

from .models import Familia, Usuario


class TutorSocialAccountAdapter(
    DefaultSocialAccountAdapter
):
    """
    O login social do projeto é destinado aos responsáveis.

    Uma conta criada via Google sempre nasce como TUTOR.
    Crianças continuam usando o acesso infantil definido pelo Tutor.
    """

    def populate_user(
        self,
        request,
        sociallogin,
        data,
    ):
        usuario = super().populate_user(
            request,
            sociallogin,
            data,
        )

        usuario.tipo = Usuario.Tipo.TUTOR

        return usuario

    def save_user(
        self,
        request,
        sociallogin,
        form=None,
    ):
        usuario = super().save_user(
            request,
            sociallogin,
            form,
        )

        usuario.tipo = Usuario.Tipo.TUTOR

        campos = [
            "tipo",
        ]

        if not usuario.first_name:
            nome_google = (
                sociallogin.account.extra_data.get(
                    "given_name",
                    "",
                )
                or sociallogin.account.extra_data.get(
                    "name",
                    "",
                )
            ).strip()

            if nome_google:
                usuario.first_name = nome_google
                campos.append(
                    "first_name"
                )

        usuario.save(
            update_fields=campos
        )

        familia = (
            usuario
            .familias_como_tutor
            .first()
        )

        if familia is None:
            nome = (
                usuario.first_name
                or usuario.username
                or "Responsável"
            )

            familia = Familia.objects.create(
                nome=f"Família de {nome}"
            )

            familia.tutores.add(
                usuario
            )

        return usuario
