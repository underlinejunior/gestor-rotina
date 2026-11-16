# ROTINA CONECTA — VERSÃO DE RECONSTRUÇÃO LIMPA

**IMPORTANTE: leia primeiro `INSTALACAO_DO_ZERO.md`.** Esta versão utiliza UUID e exige recriar as migrações e o banco PostgreSQL a partir do esquema atual. Não execute `migrate` diretamente num banco antigo.

---

# Rotina Conecta

Aplicação web progressiva (PWA) gamificada, desenvolvida como projeto acadêmico do Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas do IFPI — Campus Parnaíba. Apoia o planejamento e o acompanhamento familiar das rotinas infantis, com supervisão de um Tutor.

> **Escopo:** as *Skills* são categorias de organização e progressão gamificada das atividades; não medem desenvolvimento infantil e não têm finalidade diagnóstica. O projeto é um protótipo acadêmico, não um serviço público homologado.

## Como funciona

1. O Tutor cadastra a família e os perfis das crianças, com acesso próprio opcional para cada criança.
2. O Tutor cria moldes recorrentes, replica rotinas, cadastra tarefas bônus ou utiliza sugestões do catálogo e da IA; sugestões dependem de sua confirmação.
3. O sistema cria instâncias das tarefas previstas. O processamento ocorre em determinados acessos à aplicação e também pode ser iniciado por comando de gerenciamento.
4. A Criança registra a realização **com fotografia obrigatória**. A tarefa passa para **Em revisão**; a fotografia não concede pontos automaticamente.
5. O Tutor aprova ou rejeita. A aprovação libera pontos, XP histórico e XP das Skills associadas. Na rejeição pode haver feedback e novo envio.
6. Tarefas de datas anteriores que permaneçam **Pendentes** ou **Rejeitadas** podem ser encerradas como **Não realizadas**, com penalidade única de 50% dos pontos-base, arredondada para cima. Tarefas **Em revisão** não sofrem penalidade apenas por aguardar o Tutor.
7. A Criança pode solicitar recompensas quando possuir saldo suficiente. Resgates e penalidades afetam o saldo de pontos, mas não apagam XP histórico. O saldo pode ficar negativo devido às penalidades.

## Perfis e permissões

- **Tutor:** administra as rotinas e recompensas, analisa evidências, acompanha Skills e relatórios e gerencia dados familiares. Seu acesso é limitado às famílias às quais está vinculado.
- **Criança:** consulta seu painel, registra evidências, acompanha gamificação e solicita recompensas, dentro das permissões do perfil. O acesso próprio é opcional.
- **Google OAuth:** integração externa para autenticação do Tutor.
- **API Gemini:** recurso externo e experimental para sugestões, sujeito às condições do provedor e à confirmação do Tutor.

## Funcionalidades e requisitos (IDs do RTS revisado)

| ID | Funcionalidade |
|---|---|
| RF01A / RF01B | Cadastro e autenticação local do Tutor / autenticação Google |
| RF02 / RF03 | Vínculos familiares / perfis infantis e acesso próprio opcional |
| RF04 / RF05 / RF06 | Moldes de rotina / sugestões do catálogo / replicação |
| RF07 / RF08 | Tarefas bônus / geração recorrente |
| RF09 / RF10 / RF11 | Painel infantil / envio obrigatório de fotografia / avaliação pelo Tutor |
| RF12 / RF13 | Crédito de pontos e XP / encerramento e penalidade de tarefas não realizadas |
| RF14 / RF15 | Evolução das Skills / gamificação (avatar, níveis, sequência e conquistas) |
| RF16 / RF17 | Catálogo e solicitação de resgate de recompensas |
| RF18 / RF19 | Notificações internas / relatório de acompanhamento |
| RF20 | Interface inicial offline limitada, sem disponibilizar dados privados offline |
| RF21A–RF21D | Aceite de política, exportação de dados, exclusão/anonimização e retenção das evidências |
| RF22 | Sugestões com IA sujeitas à revisão e confirmação do Tutor |

Os comportamentos detalhados e as regras RN01–RN17 estão especificados no RTS. **IDs antigos presentes nos nomes de testes não correspondem aos IDs atuais dos requisitos.** Consulte [TESTES_REQUISITOS.md](TESTES_REQUISITOS.md) para essa correspondência.

## Organização do código

```text
config/        Configurações, rotas gerais e implantação
usuarios/      Autenticação, famílias, crianças e privacidade
tarefas/       Moldes, instâncias, sugestões, evidências e revisão
gamificacao/   Skills, pontos, XP, conquistas, notificações e recompensas
templates/     Interfaces renderizadas no servidor
static/        CSS, JavaScript, ícones e manifesto PWA
```

- `usuarios/models.py`: `Usuario` (herda de `AbstractUser`), `Familia`, `PerfilCrianca`, `ConviteTutor`.
- `tarefas/models.py`: `MoldeTarefa`, `InstanciaTarefa`, `SugestaoTarefa`.
- `gamificacao/models.py`: `Skill`, associações de Skills, `ProgressoSkill`, `MovimentoSkill`, `MovimentoPontos`, `Recompensa`, `ResgateRecompensa`, `Conquista`, `ConquistaCrianca`, `NotificacaoSistema`.

Uma instância de tarefa pode permanecer mesmo após a remoção do molde de origem. Atribuições de pontos e XP e resgates são tratadas por serviços específicos de negócio.

## Tecnologias

Python, Django, Django ORM, PostgreSQL, django-allauth (Google OAuth), HTML, CSS, Bootstrap, JavaScript, Pillow e PWA (manifesto e Service Worker). A integração Gemini é opcional/experimental. O sistema não pretende operar integralmente offline: a interface alternativa não disponibiliza os dados familiares protegidos.

## Instalação local (PowerShell)

Pré-requisitos: Python, PostgreSQL e dependências do projeto.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure no `.env` a `DJANGO_SECRET_KEY`, as variáveis `POSTGRES_*` e outras opções necessárias ao ambiente; crie previamente o banco PostgreSQL correspondente.

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

Acesso local usual: `http://127.0.0.1:8000/`.

Os comandos de carga/sincronização de catálogos, se necessários ao ambiente, incluem:

```powershell
python manage.py carregar_catalogo_habilidades
python manage.py sincronizar_experiencia
python manage.py recalcular_conquistas
```

Para login Google, configure `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` e o callback autorizado no provedor. Para sugestões com Gemini, são necessárias configuração e condições de uso compatíveis com o serviço.

## Processamentos por data e manutenção

A aplicação dispõe do serviço `processar_rotinas()`, chamado em determinados fluxos de acesso às páginas. Ele gera as instâncias previstas, encerra tarefas antigas em estados elegíveis e processa lembretes/resumos. **Isso não garante execução em horário fixo quando ninguém acessa a aplicação.**

```powershell
python manage.py gerar_tarefas_diarias
python manage.py processar_lembretes
python manage.py limpar_evidencias_antigas
python manage.py limpar_evidencias_antigas --dias 180
```

- `gerar_tarefas_diarias`: processa geração e encerramento conforme a data.
- `processar_lembretes`: processa notificações conforme as regras implementadas.
- `limpar_evidencias_antigas`: apaga arquivos de evidência elegíveis após o prazo configurado (padrão do comando: 180 dias), **preservando registros e histórico textual**.

Para execução independente dos acessos, esses comandos devem ser acionados por um agendador de infraestrutura configurado (por exemplo, cron). A presença dos comandos **não comprova agendamento ativo em produção**.

## Privacidade e segurança

O código inclui controle de acesso por família, proteção CSRF, entrega autorizada de evidências, política restritiva de cache para fotografias privadas, regravação das imagens com Pillow para eliminar metadados desnecessários, rotinas de retenção, exportação e exclusão/anonimização. Em produção, segredos e configurações sensíveis devem ser fornecidos pelo ambiente e a comunicação deve ser protegida por HTTPS.

Esses mecanismos não equivalem a uma certificação integral de conformidade com a LGPD. Disponibilização pública exige revisão operacional, jurídica e de segurança, incluindo condições de uso de IA e dados infantis.

## Testes e limitações de validação

```powershell
python manage.py check
python manage.py test
python manage.py test usuarios tarefas gamificacao -v 2
```

Os testes automatizados existentes cobrem fluxos selecionados de autenticação, rotinas, evidências, aprovação, penalidades, Skills, recompensas e privacidade. **A documentação não declara uma quantidade de testes aprovados nem resultados de execução não comprovados.** Veja [TESTES_REQUISITOS.md](TESTES_REQUISITOS.md).

Ainda são necessárias verificações específicas de responsividade real, instalabilidade do PWA e ambiente de produção. Não houve validação de eficácia pedagógica, clínica, psicológica ou comportamental com famílias.

## Escopo excluído

Bloqueio de aplicativos, controle do tempo de tela do sistema operacional, minijogos complexos e avaliação psicológica ou diagnóstica.

## Autoria

Evaldo Carlos da Silva Júnior — Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas, IFPI — Campus Parnaíba (2026).
