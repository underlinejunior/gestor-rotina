from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ConviteTutor, Familia, PerfilCrianca, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Perfil no sistema",
            {"fields": ("tipo", "boas_vindas_exibidas")},
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Perfil no sistema",
            {"fields": ("tipo",)},
        ),
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "tipo",
        "boas_vindas_exibidas",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "tipo",
        "boas_vindas_exibidas",
        "is_staff",
        "is_active",
    )


@admin.register(Familia)
class FamiliaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "criada_em",
    )

    search_fields = ("nome",)


@admin.register(PerfilCrianca)
class PerfilCriancaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "familia",
        "avatar_tipo",
        "acesso_proprio",
        "usuario",
        "saldo_pontos",
    )

    list_filter = (
        "familia",
        "avatar_tipo",
        "acesso_proprio",
    )

    search_fields = (
        "nome",
        "usuario__username",
    )


@admin.register(ConviteTutor)
class ConviteTutorAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "familia",
        "criado_por",
        "ativo",
        "expira_em",
        "usado_por",
    )

    list_filter = (
        "ativo",
        "expira_em",
    )

    search_fields = (
        "codigo",
        "familia__nome",
        "criado_por__username",
        "usado_por__username",
    )
