# Rotina Conecta

Aplicação web gamificada para apoiar famílias na organização de rotinas infantis e no acompanhamento das atividades cotidianas.

O **Rotina Conecta** foi desenvolvido como Trabalho de Conclusão de Curso do Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas do IFPI – Campus Parnaíba. A proposta combina planejamento de tarefas, acompanhamento familiar, evidências de realização, gamificação, Skills, recompensas, relatórios e sugestões de tarefas pelo catálogo do sistema ou por inteligência artificial.

> As **Skills** são categorias gamificadas usadas para organizar e acompanhar a frequência de práticas associadas às tarefas. Elas não constituem avaliação psicológica, pedagógica, clínica ou diagnóstico da criança.

---

## 1. Visão geral

```text
Tutor cria ou escolhe uma tarefa
            ↓
Define frequência, horário e Skills
            ↓
Sistema gera a tarefa no período previsto
            ↓
Criança consulta a rotina e realiza a atividade
            ↓
Registra a realização e, quando exigido, envia foto
            ↓
Tutor revisa
       ↙          ↘
   Aprova        Rejeita
      ↓              ↓
Pontos + XP      Feedback / nova tentativa
      ↓
Skills + evolução gamificada
      ↓
Recompensas + histórico + relatórios
```

Quando uma tarefa é encerrada sem realização, o sistema registra a ocorrência e aplica a regra de penalidade prevista.

---

## 2. Perfis e atores

### Tutor / Responsável

O Tutor administra a família e pode:

- criar e editar perfis infantis;
- vincular outros responsáveis à família;
- criar, editar, ativar, desativar e remover rotinas;
- cadastrar tarefas bônus;
- utilizar sugestões do sistema;
- solicitar sugestões com inteligência artificial;
- definir Skills de ênfase;
- revisar evidências;
- aprovar ou rejeitar tarefas;
- gerenciar recompensas;
- acompanhar Skills, evolução e relatórios;
- utilizar recursos de privacidade e gestão de dados.

### Criança

O acesso próprio da Criança é opcional e depende da configuração realizada pelo responsável.

Quando habilitado, a Criança pode:

- acessar seu painel;
- consultar tarefas e status;
- registrar a realização das atividades;
- enviar evidências quando exigidas;
- acompanhar pontos, XP, Skills, nível e conquistas;
- solicitar resgate de recompensas;
- receber notificações internas.

### Serviços externos e automáticos

- **Google OAuth:** autenticação social do Tutor;
- **Serviço de IA:** geração de sugestões de tarefas;
- **Agendador:** geração automática de tarefas e processamento de eventos periódicos.

---

## 3. Funcionalidades implementadas

| Área | Situação |
|---|---|
| Autenticação por usuário e senha | ✅ Implementado |
| Login Google para Tutor | ✅ Implementado |
| Família com múltiplos responsáveis | ✅ Implementado |
| Perfis infantis e acesso próprio opcional | ✅ Implementado |
| Rotinas recorrentes | ✅ Implementado |
| Tarefas bônus | ✅ Implementado |
| Geração automática de tarefas | ✅ Implementado |
| Cadastro guiado de rotina | ✅ Implementado |
| Cadastro manual de tarefa | ✅ Implementado |
| Sugestões do catálogo do sistema | ✅ Implementado |
| Sugestões com inteligência artificial | ✅ Implementado |
| Priorização por idade e contexto da rotina | ✅ Implementado |
| Equilíbrio automático de Skills | ✅ Implementado |
| Seleção de até três Skills de ênfase | ✅ Implementado |
| Replicação da rotina para todas as crianças | ✅ Implementado |
| Painel infantil | ✅ Implementado |
| Evidência fotográfica | ✅ Implementado |
| Revisão pelo Tutor | ✅ Implementado |
| Pontuação e penalidade | ✅ Implementado |
| Saldo de pontos separado do XP histórico | ✅ Implementado |
| Skills e XP por Skill | ✅ Implementado |
| Avatar, nível, sequência e conquistas | ✅ Implementado |
| Recompensas personalizadas e resgates | ✅ Implementado |
| Notificações e lembretes internos | ✅ Implementado |
| Relatórios para impressão/PDF | ✅ Implementado |
| PWA instalável | ✅ Implementado |
| Central de Privacidade | ✅ Implementado |
| Exportação de dados | ✅ Implementado |
| Exclusão/anonimização | ✅ Implementado |
| Retenção configurável de evidências | ✅ Implementado |
| Remoção de metadados EXIF/GPS | ✅ Implementado |
| Evidências servidas por rota autenticada | ✅ Implementado |
| Testes automatizados dos principais fluxos | ✅ Implementado |
| Deploy público de produção | ⏳ Pendente de consolidação |

---

## 4. Cadastro de rotinas

O cadastro de rotina é realizado por um fluxo guiado. Na escolha da tarefa, o Tutor possui três caminhos:

### 4.1 Informar manualmente
O Tutor define diretamente os dados da atividade.

### 4.2 Sugestões do sistema
O catálogo interno oferece tarefas adequadas à faixa etária e ao contexto da rotina.

O sistema pode considerar idade, tarefas já cadastradas, Skills selecionadas, Skills pouco trabalhadas e repetição excessiva de determinadas categorias.

### 4.3 Sugestões com inteligência artificial
A IA atua somente como apoio:

```text
Sistema prepara o contexto
          ↓
IA devolve sugestões
          ↓
Tutor analisa
          ↓
Tutor aceita, edita ou ignora
          ↓
Somente após confirmação a rotina é cadastrada
```

A sugestão de IA não é persistida automaticamente.

---

## 5. Skills e ênfase

As tarefas podem ser associadas a uma ou mais Skills com intensidade configurável:

- Autonomia;
- Organização;
- Responsabilidade;
- Constância;
- Autocuidado;
- Foco;
- Colaboração;
- Iniciativa.

O sistema registra XP por Skill, apresenta histórico, pode identificar categorias pouco trabalhadas, reduzir repetição excessiva, equilibrar recomendações e permitir ao Tutor escolher até três Skills de ênfase.

A mesma ênfase orienta o catálogo interno e o contexto utilizado nas sugestões por IA.

> As Skills representam categorias de acompanhamento das tarefas realizadas e não possuem finalidade diagnóstica.

---

## 6. Realização e validação

Quando uma tarefa permite ou exige evidência, a Criança pode registrar a realização com uma fotografia.

```text
Tarefa disponível
      ↓
Criança realiza
      ↓
Envia evidência
      ↓
Em revisão
      ↓
Tutor aprova ou rejeita
```

Somente a aprovação libera pontuação, XP e evolução das Skills. Em caso de rejeição, o Tutor pode registrar feedback para nova tentativa.

---

## 7. Pontos, XP e penalidades

### Saldo de pontos
Pode aumentar com tarefas aprovadas e diminuir com penalidades ou resgates.

### XP histórico
Representa a trajetória gamificada da Criança e não é consumido quando os pontos são gastos.

### XP das Skills
É registrado separadamente conforme as Skills associadas e a intensidade configurada.

### Penalidade
Uma tarefa encerrada como não realizada deduz metade dos pontos-base, com arredondamento para cima quando necessário.

---

## 8. Recompensas

O Tutor pode cadastrar recompensas personalizadas, inclusive experiências familiares, com nome, descrição, categoria, custo em pontos e disponibilidade.

A Criança pode solicitar resgate quando possui saldo suficiente. O resgate reduz o saldo, mas não reduz XP histórico nem XP das Skills.

---

## 9. Relatórios e acompanhamento

O relatório por Criança reúne informações como tarefas realizadas, pendências, movimentação de pontos, evolução gamificada, Skills mais e menos presentes e indicadores da rotina.

Pode ser utilizado para impressão ou geração de PDF pelo navegador.

---

## 10. Privacidade e segurança

O projeto incorpora:

- autenticação e autorização por família;
- restrição de recursos administrativos ao Tutor correspondente;
- proteção CSRF;
- evidências por rota autenticada e autorizada;
- regravação de imagens;
- remoção de metadados EXIF/GPS;
- limitação de tamanho e resolução;
- retenção configurável;
- exportação de dados;
- exclusão ou anonimização;
- cookies seguros e HTTPS quando o modo de produção está ativo;
- chave secreta e hosts permitidos configuráveis por ambiente;
- cache conservador para conteúdo autenticado.

> Esses controles não representam certificação de conformidade integral com a LGPD. Uma implantação pública exige também governança, política operacional de segurança, definição de responsabilidades, resposta a incidentes, backups testados e avaliação periódica de riscos.

### Uso de inteligência artificial

A IA é um serviço externo de apoio. O Tutor continua responsável pela escolha final da tarefa e as sugestões não são salvas sem confirmação explícita.

Antes de uma implantação pública com dados reais, devem ser revisadas as condições de tratamento do provedor e as informações da política de privacidade.

---

## 11. PWA

O Rotina Conecta funciona como **Progressive Web Application (PWA)** e possui:

- manifesto;
- ícones;
- service worker;
- modo standalone;
- instalação em navegadores compatíveis;
- interface responsiva;
- shell offline.

---

## 12. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | Permitir cadastro e autenticação do Tutor por credenciais locais e Google |
| RF02 | Vincular múltiplos responsáveis a uma mesma família |
| RF03 | Gerenciar perfis infantis e acesso próprio opcional |
| RF04 | Criar, editar, ativar/desativar e remover rotinas recorrentes |
| RF05 | Apresentar sugestões do catálogo considerando faixa etária e Skills |
| RF06 | Replicar uma rotina para todas as crianças da família |
| RF07 | Criar tarefas bônus imediatas |
| RF08 | Gerar tarefas automaticamente conforme frequência e dias configurados |
| RF09 | Permitir à Criança consultar seu painel, tarefas e status |
| RF10 | Registrar fotografia como evidência de realização |
| RF11 | Permitir ao Tutor revisar, aprovar ou rejeitar a realização |
| RF12 | Processar pontuação e penalidade conforme as regras de negócio |
| RF13 | Associar tarefas a Skills, registrar XP e acompanhar equilíbrio entre categorias |
| RF14 | Apresentar avatar, nível, sequência, conquistas e celebrações |
| RF15 | Gerenciar recompensas e resgates |
| RF16 | Gerar alertas, lembretes e notificações internas |
| RF17 | Gerar relatório de acompanhamento por Criança |
| RF18 | Permitir instalação como PWA em dispositivos compatíveis |
| RF19 | Disponibilizar recursos de privacidade e gestão de dados |
| RF20 | Gerar sugestões com IA considerando contexto, histórico e Skills de prioridade |

---

## 13. Regras de negócio principais

- **RN01 — Histórico:** alterações em uma rotina não modificam tarefas passadas.
- **RN02 — Aprovação:** enviar foto não concede pontos; somente a aprovação do Tutor libera pontuação.
- **RN03 — Atraso:** atraso/procrastinação é indicador separado da penalidade.
- **RN04 — Penalidade:** tarefa não realizada deduz metade dos pontos-base.
- **RN05 — Saldo x XP:** resgates e penalidades alteram saldo, mas não apagam XP histórico.
- **RN06 — Skills:** XP das Skills é separado da pontuação geral.
- **RN07 — Recompensas:** resgate depende de saldo suficiente e não reduz XP histórico.
- **RN08 — Família:** o Tutor só pode acessar e modificar dados da própria família.
- **RN09 — Evidência privada:** fotos são entregues apenas por rota autenticada e autorizada.
- **RN10 — Retenção:** evidências finalizadas podem ser removidas após o prazo configurado.
- **RN11 — Privacidade:** o Tutor pode exportar dados e solicitar exclusão/anonimização.
- **RN12 — IA:** sugestões não são persistidas sem revisão e confirmação do Tutor.
- **RN13 — Priorização de Skills:** o sistema pode equilibrar Skills ou seguir até três Skills escolhidas como ênfase.

---

## 14. Tecnologias

### Backend
- Python
- Django 5.2
- Django ORM
- django-allauth

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- Bootstrap Icons
- JavaScript

### Banco de dados

```text
PostgreSQL
```

O projeto usa PostgreSQL em desenvolvimento, testes e produção. A conexão é configurada pelas variáveis `POSTGRES_*` do arquivo `.env`.

### Imagens
- Pillow
- Django `ImageField`

### Integrações
- Google OAuth
- API Gemini

---

## 15. Estrutura resumida

```text
gestor-rotinas/
├── config/
├── usuarios/
├── tarefas/
├── gamificacao/
├── templates/
├── static/
├── media/
├── .env.example
├── requirements.txt
├── manage.py
└── README.md
```

---

## 16. Instalação local

### Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
pip install -r requirements.txt
```

Crie o arquivo de ambiente a partir do modelo:

```powershell
Copy-Item .env.example .env
```

Configure no `.env` pelo menos `DJANGO_SECRET_KEY` e as credenciais `POSTGRES_*`. Crie o banco PostgreSQL informado em `POSTGRES_DB` e depois aplique as migrations:

```powershell
python manage.py migrate
```

Atualize catálogos e dados derivados quando necessário:

```powershell
python manage.py carregar_catalogo_habilidades
python manage.py sincronizar_experiencia
python manage.py recalcular_conquistas
```

Verifique:

```powershell
python manage.py check
```

Execute:

```powershell
python manage.py runserver
```

Acesse:

```text
http://127.0.0.1:8000/
```

---

## 17. Google OAuth

O projeto utiliza `django-allauth`.

Variáveis utilizadas:

```text
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
```

Callback de desenvolvimento:

```text
http://127.0.0.1:8000/accounts/google/login/callback/
```

O acesso Google é destinado ao Tutor.

---

## 18. Processos periódicos

### Geração de tarefas

```powershell
python manage.py gerar_tarefas_diarias
```

### Lembretes

```powershell
python manage.py processar_lembretes
```

Em produção, esses comandos devem ser executados por um mecanismo de agendamento.

---

## 19. Testes

Execute a suíte do Django com:

```powershell
python manage.py test
```

A validação técnica deve cobrir especialmente autenticação, isolamento entre famílias, permissões, geração de tarefas, evidências, revisão, pontuação, Skills, recompensas, privacidade, mídia protegida, remoção de metadados e exportação/exclusão de dados.

---

## 20. Estado para produção

A aplicação funciona como protótipo acadêmico funcional e já está configurada para PostgreSQL. Antes de disponibilização pública, devem ser consolidados:

- HTTPS;
- armazenamento de mídia;
- gestão de segredos;
- proteção contra tentativas repetidas de login;
- registros de auditoria;
- backups e testes de restauração;
- monitoramento e logs;
- resposta a incidentes;
- governança de privacidade;
- revisão do uso de IA com dados reais;
- verificação final de segurança do ambiente de produção.

---

## 21. Fora do escopo atual

Não são objetivos centrais:

- bloqueio de aplicativos;
- controle do tempo de tela do sistema operacional;
- `AccessibilityService`;
- minijogos complexos;
- avaliação psicológica;
- diagnóstico infantil.

O foco permanece em **gestão de rotinas, acompanhamento familiar, gamificação e organização do histórico das atividades**.

---

## 22. Objetivo acadêmico

O Rotina Conecta foi desenvolvido como **Relatório Técnico de Software** do Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas do IFPI – Campus Parnaíba.

O objetivo geral é desenvolver e validar tecnicamente uma aplicação web progressiva gamificada capaz de apoiar a organização de rotinas infantis e o acompanhamento familiar, reunindo planejamento de tarefas, registro de realização, validação pelo responsável, proteção das evidências e visualização do progresso da criança.

---

## Licença

Projeto acadêmico em desenvolvimento.

---

## Autor

**Evaldo Carlos da Silva Júnior**  
Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas  
Instituto Federal de Educação, Ciência e Tecnologia do Piauí — Campus Parnaíba  
2026
