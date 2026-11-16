"""Recria o esquema PostgreSQL e as migrações iniciais para uma instalação nova.

Uso: python scripts/reiniciar_banco.py --confirmar ZERAR_ROTINA_CONECTA
ATENÇÃO: apaga TODAS as tabelas no esquema public do banco configurado.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description="Reset destrutivo do PostgreSQL do Rotina Conecta")
    parser.add_argument("--confirmar", help="Digite ZERAR_ROTINA_CONECTA")
    parser.add_argument("--apagar-midias", action="store_true", help="Remove também os comprovantes locais")
    args = parser.parse_args()
    if args.confirmar != "ZERAR_ROTINA_CONECTA":
        parser.error("Reset cancelado: é obrigatória a confirmação explícita.")

    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')

    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    from django.conf import settings
    from django.db import connection, transaction

    db = settings.DATABASES['default']
    if db['ENGINE'] != 'django.db.backends.postgresql':
        raise SystemExit('O script só aceita o PostgreSQL configurado no projeto.')
    host = str(db.get('HOST') or '').lower()
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise SystemExit('Reset bloqueado em servidor remoto; faça procedimento supervisionado.')
    name = str(db['NAME'])
    if name.lower() in ('postgres','template0','template1'):
        raise SystemExit('Banco reservado do PostgreSQL: reset recusado.')

    print(f'BANCO QUE SERÁ TOTALMENTE APAGADO: {name} em {host}')
    print('A operação apaga TODAS as tabelas do esquema public desse banco.')
    typed = input(f'Para confirmar, escreva o nome exato do banco ({name}): ').strip()
    if typed != name:
        raise SystemExit('Nome diferente. Nenhum dado foi apagado.')

    # Validação do destino; usa credenciais e conexão Django do próprio projeto.
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database(), inet_server_addr()::text')
            actual, _ = cursor.fetchone()
            if actual != name:
                raise RuntimeError('O banco aberto não corresponde ao banco confirmado.')
            cursor.execute('DROP SCHEMA public CASCADE')
            cursor.execute('CREATE SCHEMA public')
            cursor.execute('GRANT USAGE, CREATE ON SCHEMA public TO PUBLIC')
    connection.close()

    if args.apagar_midias:
        import shutil
        midias = Path(settings.MEDIA_ROOT).resolve()
        if midias != (ROOT / 'media').resolve():
            raise RuntimeError('MEDIA_ROOT inesperado: remoção de arquivos bloqueada.')
        if midias.exists():
            shutil.rmtree(midias)

    def cmd(*arguments):
        subprocess.run([sys.executable, str(ROOT / 'manage.py'), *arguments], cwd=ROOT, check=True)

    # Nada de migrações legadas: gera a estrutura a partir dos modelos atuais.
    cmd('makemigrations', 'usuarios', 'tarefas', 'gamificacao')
    cmd('migrate')
    cmd('check')
    print('\nBanco reconstruído. Crie um tutor via cadastro ou admin com createsuperuser.')
    print('Sugestão: python manage.py carregar_catalogo_habilidades')
    print('Depois: python manage.py test usuarios tarefas gamificacao')


if __name__ == '__main__':
    main()
