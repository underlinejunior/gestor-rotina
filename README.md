# Minha Rotina

Aplicação web gamificada para gerenciamento de rotinas infantis, desenvolvida como projeto de Trabalho de Conclusão de Curso.

O **Minha Rotina** permite que responsáveis criem e acompanhem rotinas, enquanto crianças realizam atividades, enviam evidências, acumulam pontos, evoluem avatares, desenvolvem Skills gamificadas e resgatam recompensas.

O sistema foi pensado para unir:

- organização da rotina;
- acompanhamento familiar;
- gamificação;
- reforço positivo;
- autonomia progressiva;
- registro histórico;
- visualização de evolução;
- sugestões de tarefas adequadas à idade.

> As Skills apresentadas no sistema são **indicadores gamificados de prática de atividades**. Elas não constituem avaliação psicológica, pedagógica, clínica ou diagnóstico da criança.

---

# 1. Visão geral do fluxo

```text
Tutor cria ou escolhe uma tarefa
          ↓
Define frequência, horário e Skills
          ↓
Sistema gera a tarefa no dia previsto
          ↓
Criança realiza a atividade
          ↓
Envia foto como evidência
          ↓
Tutor revisa
      ↙         ↘
  Aprova       Rejeita
     ↓
Libera pontos
     ↓
Saldo + XP + Skills
     ↓
Avatar / Conquistas / Streak
     ↓
Recompensas e histórico
```

Se a tarefa não for concluída dentro do prazo, o sistema registra a ocorrência e aplica a penalidade definida pela regra de negócio.

---

# 2. Status atual

| Área | Situação |
|---|---|
| Autenticação Tutor/Criança | ✅ Implementado |
| Login com Google para Tutor | ✅ Implementado |
| Perfis infantis | ✅ Implementado |
| Mais de um responsável | ✅ Implementado |
| Rotinas diárias e semanais | ✅ Implementado |
| Tarefas bônus | ✅ Implementado |
| Tarefas pré-definidas com ícones | ✅ Implementado |
| Sugestões por idade | ✅ Implementado |
| Replicar tarefa para todas as crianças | ✅ Implementado |
| Manhã / tarde / noite / horário específico | ✅ Implementado |
| Lembretes internos | ✅ Implementado |
| Foto como evidência | ✅ Implementado |
| Revisão pelo Tutor | ✅ Implementado |
| Pontos e penalidades | ✅ Implementado |
| XP histórico do avatar | ✅ Implementado |
| Skills / Habilidades | ✅ Implementado |
| Radar de Skills | ✅ Implementado |
| Histórico e indicadores | ✅ Implementado |
| Notificações | ✅ Implementado |
| PWA instalável | ✅ Implementado |
| Loja de recompensas | ✅ Implementado |
| Resgate de recompensas | ✅ Implementado |
| Sequência de dias (streak) | ✅ Implementado |
| Conquistas / badges | ✅ Implementado |
| Celebrações visuais | ✅ Implementado |
| Relatório semanal impresso / PDF | ✅ Implementado |
| Gemini / sugestões personalizadas por IA | ⏳ Planejado |
| Cofrinho / meta de recompensa | ⏳ Planejado |
| Push notification real | ⏳ Planejado |
| Assistente por lacunas de Skills | ⏳ Planejado |
| Deploy de produção | ⏳ Planejado |

---

# 3. Funcionalidades implementadas

## 3.1 Autenticação e acesso

O sistema possui dois tipos de usuário:

- **Tutor/Responsável**
- **Criança**

O Tutor pode:

- criar conta;
- entrar com usuário e senha;
- entrar com Google;
- criar e editar perfis infantis;
- definir se a criança terá acesso próprio.

A criança pode:

- utilizar um usuário criado pelo Tutor;
- acessar sua própria interface;
- visualizar tarefas;
- enviar evidências;
- acompanhar pontos, avatar, Skills, conquistas e recompensas.

O login com Google é reservado ao Tutor/Responsável.

---

## 3.2 Família e múltiplos responsáveis

Uma família pode possuir mais de um Tutor.

O fluxo implementado utiliza código de convite:

```text
Tutor A
  ↓
Gera código de 6 dígitos
  ↓
Tutor B entra na própria conta
  ↓
Informa o código
  ↓
Passa a compartilhar a mesma família
```

O código possui validade de 48 horas.

O sistema evita misturar automaticamente famílias que já possuam dados.

---

## 3.3 Cadastro de crianças

Cada perfil infantil pode possuir:

- nome;
- data de nascimento;
- avatar;
- acesso próprio ou não;
- usuário vinculado opcional;
- saldo de pontos;
- XP histórico;
- progresso de Skills;
- histórico de tarefas;
- conquistas;
- resgates.

Avatares atuais:

- 🤖 Robô
- 🦊 Raposa
- 🐲 Dragão
- 🧑‍🚀 Astronauta

---

# 4. Rotinas e tarefas

## 4.1 Cadastro manual

O Tutor pode cadastrar:

- tarefa;
- descrição;
- criança;
- pontos;
- frequência;
- dias da semana;
- momento do dia;
- horário específico;
- lembrete;
- Skills relacionadas;
- intensidade de cada Skill.

O campo **Tarefa** pode ser usado de duas maneiras:

1. escolher uma tarefa pré-definida;
2. digitar uma tarefa personalizada.

---

## 4.2 Tarefas pré-definidas

O sistema possui catálogo local com ícones e tarefas básicas.

Exemplos:

```text
🛏️ Arrumar a cama
🎒 Organizar a mochila
🪥 Escovar os dentes
🧺 Colocar a roupa suja no cesto
📖 Fazer um bloco de leitura
🧹 Ajudar em uma tarefa doméstica
🍽️ Levar o prato até a pia
📅 Organizar os compromissos da semana
```

As sugestões possuem:

- ícone;
- nome;
- descrição;
- idade mínima e máxima;
- pontos sugeridos;
- frequência;
- dias;
- Skills;
- intensidade das Skills.

---

## 4.3 Sugestões por idade

Quando o Tutor seleciona a criança, o sistema utiliza a data de nascimento para filtrar sugestões adequadas à idade.

Exemplo:

```text
🎒 Organizar a mochila para a escola
10 pontos

📋 Organização +++
✅ Responsabilidade ++
🌱 Autonomia ++
```

Ao escolher uma sugestão, o formulário pode preencher automaticamente:

- tarefa;
- descrição;
- pontos;
- frequência;
- dias;
- Skills;
- intensidade das Skills.

O Tutor pode alterar qualquer informação antes de salvar.

---

## 4.4 Replicação para todas as crianças

No cadastro de nova rotina existe a opção:

```text
Replicar para todas as crianças
```

Ao ativá-la, o sistema cria a mesma rotina para todos os perfis da família, mantendo:

- tarefa;
- descrição;
- pontos;
- frequência;
- dias;
- momento;
- horário;
- Skills;
- intensidade.

---

## 4.5 Frequência

As rotinas podem ser:

- diárias;
- semanais.

Nas semanais, o Tutor escolhe os dias desejados.

---

## 4.6 Momento do dia

Uma tarefa pode ser classificada como:

- Qualquer horário
- 🌅 Manhã
- ☀️ Tarde
- 🌙 Noite
- 🕐 Horário específico

Horários padrão utilizados para lembretes internos:

```text
Manhã → 08:00
Tarde → 15:00
Noite → 19:00
```

Quando é usado **Horário específico**, o sistema utiliza o horário informado pelo Tutor.

---

## 4.7 Tarefas bônus

O Tutor pode criar tarefas imediatas sem criar um molde permanente.

Exemplo:

```text
🧹 Ajudar a organizar a garagem
+20 pontos
Somente hoje
```

Tarefas bônus também podem possuir Skills.

---

# 5. Geração automática

Os moldes ativos geram instâncias conforme a frequência configurada.

Comando:

```powershell
python manage.py gerar_tarefas_diarias
```

O processamento pode:

- gerar tarefas do dia;
- encerrar tarefas antigas;
- identificar tarefas não realizadas;
- aplicar penalidades;
- criar alertas;
- gerar resumos;
- processar notificações relacionadas.

---

# 6. Evidência por foto

Para marcar uma tarefa como concluída, a criança envia uma foto.

O campo utiliza:

```html
accept="image/*"
capture="environment"
```

Isso solicita/prioriza a câmera traseira em navegadores compatíveis.

> O navegador ou sistema operacional ainda pode permitir escolha da galeria. Portanto, o projeto não afirma que a galeria é bloqueada universalmente.

As fotos são organizadas por data:

```text
media/
└── comprovantes/
    └── ANO/
        └── MES/
            └── DIA/
```

---

# 7. Revisão pelo Tutor

O envio da foto não concede pontos automaticamente.

Fluxo:

```text
Pendente
   ↓
Foto enviada
   ↓
Aguardando revisão
   ↓
Tutor aprova ou rejeita
```

Na revisão, o Tutor pode:

- visualizar a foto;
- aprovar;
- rejeitar;
- fornecer feedback;
- ajustar a quantidade de pontos.

Somente a aprovação concede pontos.

---

# 8. Pontos, XP e penalidades

O sistema separa dois conceitos.

## 8.1 Saldo de pontos

O saldo pode:

- aumentar com tarefas aprovadas;
- diminuir com penalidades;
- ser utilizado na loja de recompensas.

## 8.2 XP histórico do avatar

O XP:

- registra evolução histórica;
- aumenta com tarefas aprovadas;
- não diminui quando a criança utiliza pontos;
- não é consumido em recompensas.

Isso permite:

```text
Saldo de pontos → economia / recompensas
XP histórico    → evolução do avatar
```

---

## 8.3 Penalidade por tarefa não realizada

Quando uma tarefa é encerrada como **Não realizada**, o sistema desconta 50% dos pontos-base.

Exemplo:

```text
Tarefa vale 10
Não realizada → -5 pontos
```

Quando a metade não é inteira, o valor é arredondado para cima.

Exemplo:

```text
5 pontos → -3
7 pontos → -4
15 pontos → -8
```

A penalidade é registrada no histórico de movimentações.

---

# 9. Avatar e níveis

A evolução utiliza XP histórico.

| Nível | XP | Título |
|---|---:|---|
| 1 | 0–49 | Iniciante |
| 2 | 50–149 | Explorador |
| 3 | 150–299 | Campeão |
| 4 | 300–499 | Mestre |
| 5 | 500+ | Lendário |

O sistema mostra:

- avatar;
- nível;
- título;
- barra de progresso;
- XP atual;
- XP restante;
- celebração em mudança de nível.

---

# 10. Skills / Habilidades

Além da gamificação geral, cada tarefa pode contribuir para Skills.

Skills atuais:

- 🌱 Autonomia
- 📋 Organização
- ✅ Responsabilidade
- 🔁 Constância
- 🧼 Autocuidado
- 🎯 Foco
- 🤝 Colaboração
- 💡 Iniciativa

Intensidades:

```text
+    Leve   → +3 XP
++   Médio  → +6 XP
+++  Forte  → +10 XP
```

O XP de Skill é independente dos pontos gerais.

Exemplo:

```text
🎒 Organizar mochila

10 pontos gerais

📋 Organização       +10 XP
✅ Responsabilidade   +6 XP
🌱 Autonomia          +6 XP
```

---

## 10.1 Níveis das Skills

| Nível | XP | Título |
|---|---:|---|
| 1 | 0–59 | Descobrindo |
| 2 | 60–149 | Praticando |
| 3 | 150–299 | Evoluindo |
| 4 | 300–499 | Consolidando |
| 5 | 500+ | Dominando |

---

## 10.2 Painel de Skills

A criança e o Tutor podem visualizar:

- nível por Skill;
- XP acumulado;
- barra de progresso;
- prática nos últimos 30 dias;
- XP para o próximo nível;
- gráfico radar;
- notificações de evolução.

> O painel apresenta **frequência de prática registrada**, e não mensuração psicológica da criança.

---

# 11. Snapshot e integridade histórica

Quando uma tarefa é gerada, o sistema preserva dados importantes em snapshot.

Assim, editar uma rotina futura não altera tarefas passadas.

São preservados, entre outros:

- tarefa;
- descrição;
- pontos;
- Skills;
- intensidade;
- momento;
- horário.

Isso mantém o histórico consistente.

---

# 12. Loja de recompensas

O Tutor pode criar recompensas contendo:

- ícone;
- nome;
- descrição;
- custo;
- categoria;
- disponibilidade.

Exemplos iniciais:

```text
🤗 Abraço gigante            20 ⭐
🎲 Escolher uma brincadeira  50 ⭐
🎬 Escolher o filme          80 ⭐
🍳 Cozinhar juntos          100 ⭐
🚲 Passeio especial         150 ⭐
```

A preferência do projeto é incentivar também **experiências familiares**, e não somente recompensas materiais ou mais tempo de tela.

---

## 12.1 Resgate

A criança pode solicitar uma recompensa quando possuir saldo suficiente.

O Tutor pode:

- confirmar como entregue;
- cancelar.

Se o Tutor cancelar, os pontos são devolvidos.

Novos resgates podem aparecer para o Tutor com destaque visual comemorativo.

---

# 13. Sequência de rotina — Streak

O sistema calcula:

- 🔥 sequência atual;
- 🏆 melhor sequência.

Dias sem tarefas programadas não quebram a sequência.

O dia atual com tarefas ainda abertas também não é tratado como falha antes do encerramento.

---

# 14. Conquistas / Badges

Conquistas atuais:

- 🌟 **Primeiros Passos** — primeira tarefa aprovada;
- 🎯 **Em Ritmo** — 10 tarefas aprovadas;
- 🏆 **Super Rotina** — 30 tarefas aprovadas;
- 🔥 **Constante** — 7 dias em sequência;
- 🌱 **Mais Independente** — Autonomia nível 3;
- 📋 **Superorganizado** — Organização nível 3.

Conquistas podem gerar celebração com:

- fundo escurecido;
- estrelas;
- fogos;
- confetes;
- mensagem em destaque.

---

# 15. Celebrações visuais

O sistema possui celebrações em tela cheia para eventos especiais.

Atualmente podem ser utilizadas em:

- primeiro acesso;
- evolução de avatar;
- conquista desbloqueada;
- solicitação de recompensa.

O objetivo é reforçar eventos positivos e importantes dentro da experiência.

---

# 16. Notificações

O sistema possui Central de Notificações com:

- sino;
- contador de não lidas;
- avisos recentes;
- filtro;
- marcação como lida.

Tipos implementados incluem:

- mudança de nível;
- mudança de nível de Skill;
- conquista;
- recompensa;
- tarefa não realizada;
- lembrete de tarefa;
- resumo diário;
- resumo semanal.

---

# 17. Lembretes

O sistema possui lembretes internos para rotinas.

Comando:

```powershell
python manage.py processar_lembretes
```

Em ambiente de produção, esse comando deverá ser executado periodicamente por agendador/cron.

Nesta etapa, o lembrete é interno.

**Push notification real do navegador/PWA ainda está planejada.**

---

# 18. Histórico e indicadores

O histórico pode exibir:

- tarefas;
- datas;
- status;
- pontos;
- penalidades;
- atrasos;
- XP;
- evolução;
- Skills.

Períodos utilizados:

- 7 dias;
- 30 dias;
- 90 dias.

Indicadores incluem:

- taxa de conclusão;
- aprovadas;
- não realizadas;
- pendentes;
- em revisão;
- atraso/procrastinação;
- pontos.

A taxa de conclusão considera tarefas encerradas:

```text
              aprovadas
taxa = ---------------------------
       aprovadas + não realizadas
```

---

# 19. Relatório semanal impresso / PDF

O Tutor possui relatório por criança.

Características atuais:

- formato A4 horizontal;
- impressão pelo navegador;
- opção **Salvar como PDF**;
- nome da criança em destaque;
- avatar;
- período;
- XP;
- nível;
- conclusão;
- aprovadas;
- não realizadas;
- saldo;
- pontos ganhos;
- penalidades;
- streak;
- quadro semanal;
- horário/momento;
- Skills praticadas;
- conquistas da semana.

Também é possível navegar entre:

```text
Semana anterior
Semana atual
Próxima semana
```

Para gerar PDF:

```text
Imprimir / Salvar PDF
        ↓
Destino
        ↓
Salvar como PDF
```

---

# 20. PWA

O Minha Rotina funciona como **Progressive Web App**.

Recursos:

- manifest;
- service worker;
- ícones;
- modo standalone;
- instalação na tela inicial;
- página offline;
- safe areas;
- interface responsiva.

O Service Worker evita armazenar páginas autenticadas completas no cache, reduzindo risco de exposição de dados familiares em dispositivos compartilhados.

---

# 21. Requisitos funcionais originais

| Código | Requisito | Situação |
|---|---|---|
| RF01 | Autenticação de Tutor e Criança | ✅ |
| RF02 | Gestão de perfis infantis | ✅ |
| RF03 | Cadastro de moldes de tarefas | ✅ |
| RF04 | Tarefas bônus | ✅ |
| RF05 | Sugestão de tarefas via IA | ⏳ |
| RF06 | Geração diária de tarefas | ✅ |
| RF07 | Visualização da criança | ✅ |
| RF08 | Evidência por foto | ✅ |
| RF09 | Revisão pelo Tutor | ✅ |
| RF10 | Alertas e notificações | ✅ |

Além dos requisitos originais, o projeto já incorporou funcionalidades complementares:

- Skills;
- tarefas pré-definidas;
- sugestões por idade;
- penalidades;
- XP histórico;
- loja de recompensas;
- streaks;
- conquistas;
- vários responsáveis;
- horários;
- lembretes;
- relatório/PDF.

---

# 22. Requisitos não funcionais

| Código | Requisito | Situação |
|---|---|---|
| RNF01 | PWA instalável | ✅ |
| RNF02 | Priorizar câmera traseira | ✅ |
| RNF03 | Python + Django | ✅ |
| RNF04 | Bootstrap 5 responsivo | ✅ |
| RNF05 | Banco relacional via ORM | ✅ |
| RNF06 | Fotos organizadas por data | ✅ |

---

# 23. Regras de negócio principais

## RN01 — Histórico

Alterar ou excluir um molde não modifica tarefas históricas.

## RN02 — Aprovação obrigatória

Enviar a foto não concede pontos.

Somente aprovação do Tutor libera pontuação.

## RN03 — Procrastinação

Envios realizados após 8 horas da criação podem ser identificados como atrasados.

Esse indicador é separado da penalidade por tarefa não realizada.

## RN04 — Penalidade

Tarefa encerrada como não realizada deduz metade dos pontos-base.

## RN05 — Evolução

XP histórico do avatar não é consumido quando pontos são gastos.

## RN06 — Skills

XP de Skills é independente da quantidade de pontos gerais da tarefa.

## RN07 — Recompensas

Somente saldo disponível pode ser utilizado em resgates.

## RN08 — Integridade das Skills

As Skills são copiadas para a instância da tarefa, preservando o histórico.

---

# 24. Tecnologias

## Backend

- Python
- Django 5
- Django ORM
- django-allauth

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- Bootstrap Icons
- JavaScript

## Banco

Desenvolvimento:

```text
SQLite
```

Produção prevista:

```text
PostgreSQL
```

## Imagens

- Pillow
- Django ImageField

---

# 25. Estrutura resumida

```text
gestor-rotinas/
├── config/
├── usuarios/
├── tarefas/
├── gamificacao/
├── templates/
│   ├── usuarios/
│   ├── tarefas/
│   ├── gamificacao/
│   └── pwa/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── media/
├── manage.py
└── README.md
```

---

# 26. Instalação local

## Windows / PowerShell

Criar ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instalar dependências:

```powershell
pip install django pillow "django-allauth[socialaccount]==65.19.1"
```

Aplicar migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Atualizar catálogos e dados derivados quando necessário:

```powershell
python manage.py carregar_catalogo_habilidades
python manage.py sincronizar_experiencia
python manage.py recalcular_conquistas
```

Verificar:

```powershell
python manage.py check
```

Executar:

```powershell
python manage.py runserver
```

Abrir:

```text
http://127.0.0.1:8000/
```

---

# 27. Google OAuth

O projeto utiliza `django-allauth`.

Variáveis:

```text
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
```

Também pode ser utilizada configuração local por `.env` / `.env.local`, desde que esses arquivos não sejam enviados ao repositório.

Callback de desenvolvimento:

```text
http://127.0.0.1:8000/accounts/google/login/callback/
```

O acesso Google é destinado ao Tutor.

---

# 28. O que queremos implementar

## Prioridade alta

### 28.1 Assistente de Rotina com Gemini

Em vez de apenas gerar tarefas genéricas, a proposta é criar um **Assistente de Rotina**.

O Tutor poderá informar, por exemplo:

```text
"Meu filho tem 9 anos e sempre esquece
de preparar o material escolar."
```

O sistema poderá considerar:

- idade;
- rotinas já existentes;
- Skills;
- horários;
- comportamento/objetivo descrito;
- tarefas recentes;
- Skills pouco praticadas.

Saída esperada:

```text
🎒 Conferir mochila antes de dormir
10 pontos
📋 Organização +++
🌱 Autonomia ++

👕 Separar a roupa do dia seguinte
5 pontos
🌱 Autonomia +++
📋 Organização ++
```

A IA **não salvará tarefas automaticamente**.

Fluxo:

```text
IA sugere
   ↓
Tutor revisa
   ↓
Tutor edita
   ↓
Tutor confirma
   ↓
Rotina é criada
```

---

### 28.2 Sugestão por lacuna de Skills

O sistema poderá identificar Skills pouco praticadas.

Exemplo:

```text
Últimos 30 dias

🌱 Autonomia        78
📋 Organização      82
✅ Responsabilidade 71
🤝 Colaboração      18
💡 Iniciativa       22
```

E apresentar:

```text
"Há poucas atividades de Colaboração
na rotina atual. Quer ver sugestões?"
```

---

### 28.3 Cofrinho / Meta de recompensa

Permitir que a criança escolha uma recompensa-alvo.

Exemplo:

```text
🎯 Minha meta
🚲 Passeio especial

125 / 200 ⭐
████████████░░░░

Faltam 75 ⭐
```

Possíveis recursos:

- escolher recompensa-alvo;
- acompanhar progresso;
- guardar pontos;
- visualizar histórico;
- comemorar quando atingir a meta.

---

### 28.4 Push notifications reais

Evoluir os lembretes internos para notificações do navegador/PWA.

Possíveis eventos:

- tarefa próxima do horário;
- tarefa atrasada;
- recompensa solicitada;
- conquista;
- resumo do dia.

---

# 29. Prioridade média

## 29.1 Timer visual opcional

Exemplo:

```text
📚 Leitura
20 minutos

19:42
██████████░░
```

O timer serviria como apoio visual, sem avaliar a criança pela velocidade.

---

## 29.2 Vinculação simplificada da criança

Possível fluxo futuro:

```text
Digite o código
ou
Leia o QR Code

Quem é você?

🤖 Arthur
🦊 Sofia
🐲 Lucas
```

Isso pode reduzir a necessidade de digitar usuário e senha em dispositivos infantis.

---

## 29.3 Melhorias do relatório

Possíveis evoluções:

- resumo mensal;
- gráfico de evolução;
- comparação entre períodos;
- exportação de histórico;
- relatório consolidado da família;
- opção de quadro semanal sem indicadores, apenas para afixar/imprimir.

---

## 29.4 Recompensas mais inteligentes

Possibilidades:

- categorias personalizadas;
- limite de resgates;
- recompensa disponível somente em determinados dias;
- recompensa compartilhada entre irmãos;
- recompensas sugeridas pela IA.

---

# 30. Melhorias técnicas planejadas

- PostgreSQL em produção;
- HTTPS;
- configuração segura de variáveis de ambiente;
- armazenamento de mídia em produção;
- agendador para geração diária;
- agendador de lembretes;
- testes automatizados;
- testes multiusuário;
- auditoria de permissões;
- melhoria de acessibilidade;
- otimização do PWA;
- logs estruturados;
- backup;
- tratamento de erros em produção.

---

# 31. Funcionalidades que não são prioridade agora

Após análise de aplicativos semelhantes, algumas funcionalidades foram consideradas, mas não fazem parte do escopo imediato:

- bloqueio de aplicativos;
- controle de tempo de tela do Android;
- `AccessibilityService`;
- minijogos complexos;
- dezenas de personagens/cenários;
- controle parental do sistema operacional.

Esses recursos aumentariam muito o escopo e desviariam o projeto do foco principal: **gestão gamificada de rotinas e acompanhamento familiar**.

---

# 32. Diferenciais atuais do Minha Rotina

Entre os principais diferenciais do projeto estão:

### Tarefa + Skills

```text
🎒 Organizar mochila
        ↓
📋 Organização
✅ Responsabilidade
🌱 Autonomia
```

### XP de Skill independente

A recompensa em pontos não distorce o indicador de Skill.

### Radar de evolução

Permite visualizar quais tipos de atividade vêm sendo mais praticados.

### Sugestões por idade

O catálogo local funciona mesmo sem IA.

### Evidência + revisão

A criança não recebe pontos apenas por marcar uma tarefa.

### Saldo separado de XP

Pontos podem ser gastos sem apagar evolução.

### Recompensas familiares

A loja incentiva também experiências em família.

### PWA

O sistema pode ser utilizado sem instalação via loja de aplicativos.

### Relatório semanal

O Tutor possui uma visão imprimível / PDF do acompanhamento.

### Próximo diferencial

A integração do **Gemini com Skills e histórico** permitirá recomendações personalizadas, evitando apenas gerar listas genéricas de tarefas.

---

# 33. Posicionamento do projeto

Uma descrição adequada do sistema é:

> **Gestor gamificado de rotinas infantis que transforma atividades cotidianas em oportunidades de prática de habilidades, com acompanhamento familiar, evidências de realização, recompensas e sugestões adequadas à idade.**

Com a futura integração de IA:

> **Gestor gamificado de rotinas infantis com assistência de inteligência artificial para construção de rotinas personalizadas a partir da idade, objetivos, histórico e Skills praticadas.**

---

# 34. Objetivo acadêmico

O projeto busca desenvolver e analisar uma solução tecnológica de apoio à organização de rotinas infantis utilizando:

- gamificação;
- acompanhamento familiar;
- autonomia progressiva;
- evidência visual;
- feedback;
- reforço positivo;
- visualização de progresso;
- PWA;
- recomendação contextual.

A proposta não é diagnosticar ou mensurar características psicológicas da criança.

As Skills devem ser interpretadas como:

> **indicadores de frequência de prática de atividades associadas a determinadas habilidades.**

---

# 35. Roadmap resumido

```text
FASE ATUAL
────────────────────────────────────────
✅ Autenticação
✅ Google
✅ Perfis
✅ Rotinas
✅ Tarefas pré-definidas
✅ Sugestões por idade
✅ Foto e revisão
✅ Penalidades
✅ Skills
✅ Avatar
✅ Histórico
✅ Notificações
✅ PWA
✅ Recompensas
✅ Streak
✅ Conquistas
✅ Múltiplos responsáveis
✅ Horários e lembretes internos
✅ Relatório A4 horizontal / PDF

PRÓXIMA FASE
────────────────────────────────────────
⏳ Gemini / Assistente de Rotina
⏳ Sugestão por lacunas de Skills
⏳ Cofrinho / meta
⏳ Push notification real

FASE DE CONSOLIDAÇÃO
────────────────────────────────────────
⏳ Testes automatizados
⏳ PostgreSQL
⏳ Deploy
⏳ HTTPS
⏳ Agendamentos
⏳ Logs / backup / segurança
⏳ Melhorias de acessibilidade
```

---

# Licença

Projeto acadêmico em desenvolvimento.

---

# Autor

Projeto desenvolvido como Trabalho de Conclusão de Curso.

---

# 36. Segurança e privacidade

A versão atual inclui controles técnicos voltados à proteção dos dados familiares e infantis:

- evidências fotográficas servidas somente por endpoint autenticado e autorizado por família;
- remoção da rota pública de `/media/`;
- regravação das imagens enviadas em JPEG, sem EXIF/GPS e com resolução limitada;
- proteção CSRF nas operações de escrita;
- logout somente por `POST`;
- registro da versão da Política de Privacidade aceita pelo Tutor;
- Central de Privacidade com exportação de dados, remoção de evidências e exclusão/anomização da conta;
- política configurável de retenção de evidências;
- `SECRET_KEY`, hosts e opções de produção configuráveis por ambiente;
- HTTPS, cookies seguros e HSTS ativáveis automaticamente quando `DJANGO_DEBUG=false`;
- `.gitignore` para impedir versionamento acidental de banco local, mídia e arquivos `.env`.

Para remover evidências finalizadas acima do prazo configurado:

```powershell
python manage.py limpar_evidencias_antigas
```

O prazo padrão é de 180 dias e pode ser alterado por:

```text
EVIDENCE_RETENTION_DAYS=180
```

A existência desses controles não deve ser apresentada como certificação ou conformidade jurídica integral com a LGPD. Para disponibilização pública, continuam necessárias decisões organizacionais e jurídicas sobre hipótese legal, responsabilidades, canal de atendimento, incidentes, operadores, infraestrutura e demais obrigações aplicáveis.

**Importante no deploy:** não configure Nginx/Apache/OpenLiteSpeed para expor `MEDIA_ROOT` diretamente em `/media/`. As evidências devem continuar passando pela view autenticada `foto_tarefa_privada`.
