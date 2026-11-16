"""Validação estática que não precisa de Django ou banco conectado."""
import ast
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parent.parent
APPS = ('usuarios', 'tarefas', 'gamificacao')
ESPERADOS = {
  'usuarios': ('Usuario', 'Familia', 'PerfilInfantil', 'ConviteResponsavel'),
  'tarefas': ('RotinaPlanejada', 'TarefaAgendada', 'SugestaoAtividade'),
  'gamificacao': ('Habilidade','RotinaHabilidade','TarefaHabilidade','ProgressoHabilidade',
                  'SugestaoHabilidade','MovimentacaoHabilidade','MovimentacaoPontos',
                  'NotificacaoSistema','Recompensa','SolicitacaoResgate','Conquista','ConquistaInfantil'),
}
issues=[]
for app in APPS:
    path=ROOT/app/'models.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    models={c.name:c for c in tree.body if isinstance(c,ast.ClassDef) and any(
        isinstance(base, ast.Attribute) and base.attr=='Model' or isinstance(base,ast.Name) and base.id=='AbstractUser' for base in c.bases)}
    for name in ESPERADOS[app]:
        if name not in models:
            issues.append(f'Modelo ausente: {app}.{name}')
        elif not any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='id' for t in x.targets)
                   and isinstance(x.value,ast.Call) and getattr(x.value.func,'attr',None)=='UUIDField' for x in models[name].body):
            issues.append(f'Modelo sem UUID: {app}.{name}')
    if any(x.name!='__init__.py' for x in (ROOT/app/'migrations').glob('*.py')):
        issues.append(f'Migrações legadas encontradas: {app}')
    url=(ROOT/app/'urls.py').read_text(encoding='utf-8')
    if '<int:' in url:
        issues.append(f'URL antiga com ID inteiro: {app}')

for path in ROOT.rglob('*.py'):
    if 'migrations' in path.parts: continue
    try: ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as exc:issues.append(f'Sintaxe inválida: {path.relative_to(ROOT)}: {exc}')

if issues:
    print('\n'.join('ERRO: '+s for s in issues))
    raise SystemExit(1)
print('OK: 19 modelos com UUID, nomes UML, URLs UUID, migrações limpas e sintaxe Python.')
