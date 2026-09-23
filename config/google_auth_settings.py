import os


def _ler_env_local(base_dir):
    valores = {}

    if not base_dir:
        return valores

    for nome_arquivo in (
        ".env",
        ".env.local",
    ):
        caminho = base_dir / nome_arquivo

        if not caminho.exists():
            continue

        try:
            linhas = caminho.read_text(
                encoding="utf-8"
            ).splitlines()
        except OSError:
            continue

        for linha in linhas:
            linha = linha.strip()

            if (
                not linha
                or linha.startswith("#")
                or "=" not in linha
            ):
                continue

            chave, valor = linha.split(
                "=",
                1,
            )

            chave = chave.strip()
            valor = valor.strip().strip(
                "\"'"
            )

            if chave:
                valores.setdefault(
                    chave,
                    valor,
                )

    return valores


def aplicar_google_auth(config):
    """
    Acrescenta a configuração do django-allauth sem substituir
    o settings.py principal.

    As credenciais podem estar:
    - em variáveis de ambiente;
    - definidas antes no settings.py;
    - em .env ou .env.local;
    - em SOCIALACCOUNT_PROVIDERS['google']['APP'].
    """

    installed_apps = config.setdefault(
        "INSTALLED_APPS",
        [],
    )

    apps_necessarios = [
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
    ]

    for app in apps_necessarios:
        if app not in installed_apps:
            installed_apps.append(app)

    middleware = config.setdefault(
        "MIDDLEWARE",
        [],
    )

    account_middleware = (
        "allauth.account.middleware.AccountMiddleware"
    )

    if account_middleware not in middleware:
        auth_middleware = (
            "django.contrib.auth.middleware."
            "AuthenticationMiddleware"
        )

        if auth_middleware in middleware:
            indice = middleware.index(
                auth_middleware
            ) + 1

            middleware.insert(
                indice,
                account_middleware,
            )
        else:
            middleware.append(
                account_middleware
            )

    # allauth precisa do request context processor.
    templates = config.get(
        "TEMPLATES",
        [],
    )

    if templates:
        options = templates[0].setdefault(
            "OPTIONS",
            {},
        )

        context_processors = options.setdefault(
            "context_processors",
            [],
        )

        request_processor = (
            "django.template.context_processors.request"
        )

        if request_processor not in context_processors:
            context_processors.append(
                request_processor
            )

    config["AUTHENTICATION_BACKENDS"] = [
        "django.contrib.auth.backends.ModelBackend",
        (
            "allauth.account.auth_backends."
            "AuthenticationBackend"
        ),
    ]

    env_local = _ler_env_local(
        config.get("BASE_DIR")
    )

    providers_existentes = config.get(
        "SOCIALACCOUNT_PROVIDERS",
        {},
    )

    google_existente = (
        providers_existentes.get(
            "google",
            {},
        )
        or {}
    )

    app_existente = (
        google_existente.get(
            "APP",
            {},
        )
        or {}
    )

    client_id = (
        os.getenv(
            "GOOGLE_OAUTH_CLIENT_ID",
            "",
        ).strip()
        or str(
            config.get(
                "GOOGLE_OAUTH_CLIENT_ID",
                "",
            )
            or ""
        ).strip()
        or str(
            env_local.get(
                "GOOGLE_OAUTH_CLIENT_ID",
                "",
            )
            or ""
        ).strip()
        or str(
            app_existente.get(
                "client_id",
                "",
            )
            or ""
        ).strip()
    )

    client_secret = (
        os.getenv(
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "",
        ).strip()
        or str(
            config.get(
                "GOOGLE_OAUTH_CLIENT_SECRET",
                "",
            )
            or ""
        ).strip()
        or str(
            env_local.get(
                "GOOGLE_OAUTH_CLIENT_SECRET",
                "",
            )
            or ""
        ).strip()
        or str(
            app_existente.get(
                "secret",
                "",
            )
            or ""
        ).strip()
    )

    google_config = dict(
        google_existente
    )

    google_config.update(
        {
            "SCOPE": [
                "profile",
                "email",
            ],
            "AUTH_PARAMS": {
                "access_type": "online",
            },
            "OAUTH_PKCE_ENABLED": True,
            "EMAIL_AUTHENTICATION": True,
        }
    )

    if client_id and client_secret:
        google_config["APP"] = {
            "client_id": client_id,
            "secret": client_secret,
            "key": "",
        }

    providers = config.setdefault(
        "SOCIALACCOUNT_PROVIDERS",
        {},
    )

    providers["google"] = google_config

    config[
        "SOCIALACCOUNT_ADAPTER"
    ] = "usuarios.adapters.TutorSocialAccountAdapter"

    config[
        "SOCIALACCOUNT_AUTO_SIGNUP"
    ] = True

    config[
        "SOCIALACCOUNT_EMAIL_REQUIRED"
    ] = True

    config[
        "SOCIALACCOUNT_QUERY_EMAIL"
    ] = True

    config[
        "SOCIALACCOUNT_EMAIL_VERIFICATION"
    ] = "none"

    config[
        "SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT"
    ] = True

    config[
        "SOCIALACCOUNT_LOGIN_ON_GET"
    ] = False

    config[
        "SOCIALACCOUNT_STORE_TOKENS"
    ] = False

    # Após login social, o Tutor passa pela confirmação da política
    # de privacidade. Se já estiver na versão vigente, a própria view
    # redireciona imediatamente para o início.
    config[
        "LOGIN_REDIRECT_URL"
    ] = "/privacidade/aceite/"

    config[
        "ACCOUNT_LOGOUT_REDIRECT_URL"
    ] = "/login/"

    config[
        "GOOGLE_OAUTH_ENABLED"
    ] = bool(
        client_id
        and client_secret
    )
