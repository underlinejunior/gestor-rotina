"""Remove migrações legadas dos apps locais e gera migrações iniciais.

Não apaga banco, dados, mídia nem migrações de pacotes terceiros.
Uso: python scripts/refazer_migracoes.py --confirmar REFAZER_MIGRACOES
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
APPS = ('usuarios', 'tarefas', 'gamificacao')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirmar', default='', help='Confirmação literal REFAZER_MIGRACOES')
    args = parser.parse_args()
    encontrados = []
    for app in APPS:
        pasta = ROOT / app / 'migrations'
        if not pasta.is_dir():
            raise SystemExit(f'Pasta ausente: {pasta}')
        for arquivo in sorted(pasta.iterdir()):
            if arquivo.is_file() and arquivo.suffix == '.py' and arquivo.name != '__init__.py':
                encontrados.append(arquivo)
    print('Migrações legadas encontradas:')
    for arquivo in encontrados:
        print(' -', arquivo.relative_to(ROOT))
    if not encontrados:
        print(' - nenhuma')
    if args.confirmar != 'REFAZER_MIGRACOES':
        print('\nSimulação. Para executar, use --confirmar REFAZER_MIGRACOES')
        return
    for arquivo in encontrados:
        arquivo.unlink()
    print(f'\nRemovidas {len(encontrados)} migrações antigas.')
    subprocess.run([sys.executable, 'manage.py', 'makemigrations', *APPS], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'manage.py', 'check'], cwd=ROOT, check=True)
    print('\nMigrações novas geradas. ATENÇÃO: este script NÃO zera o banco.')
    print('Para reconstruir o PostgreSQL local dedicado, siga INSTALACAO_DO_ZERO.md.')


if __name__ == '__main__':
    main()
