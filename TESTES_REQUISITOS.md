# Matriz de rastreabilidade — requisitos x testes

Este arquivo documenta os testes automatizados incluídos no projeto para apoiar a validação técnica do **Rotina Conecta**.

Os testes foram organizados para manter rastreabilidade entre requisito, regra de negócio e evidência automatizada. Eles não substituem testes de usabilidade com participantes nem validam efeitos psicológicos, pedagógicos ou comportamentais.

## Como executar

No ambiente virtual do projeto, garanta primeiro as dependências registradas em `requirements.txt`:

```powershell
pip install -r requirements.txt
python manage.py check
python manage.py test
```

Para executar por módulo:

```powershell
python manage.py test usuarios
python manage.py test tarefas
python manage.py test gamificacao
```

Para saída mais detalhada:

```powershell
python manage.py test -v 2
```

## Requisitos funcionais

| Código | Requisito / capacidade | Evidência automatizada |
|---|---|---|
| RF01 | Autenticação de Tutor e Criança | `RF01AutenticacaoEPerfisTests.test_rf01_tutor_autentica_com_usuario_e_senha`; `test_rf01_crianca_com_acesso_proprio_autentica` |
| RF02 | Gestão e vínculo de perfis infantis | `test_rf02_perfil_pode_existir_sem_login_proprio`; `test_rf02_formulario_cria_usuario_infantil_quando_acesso_proprio_ativo`; testes de convite e isolamento entre famílias |
| RF03 | Cadastro e comportamento dos moldes de tarefas | Testes de recorrência diária/semanal, horário/lembrete e replicação para todas as crianças |
| RF04 | Tarefas bônus | `RF04RF06GeracaoESnapshotTests.test_rf04_tutor_cria_tarefa_bonus` |
| RF05 | Sugestões por IA | Testes de interpretação do JSON, filtragem de Skills inválidas e falha controlada quando a chave Gemini não está configurada |
| RF06 | Geração automática das tarefas do dia | `test_rf06_geracao_diaria_e_idempotente_e_copia_snapshot` |
| RF07 | Visualização das tarefas pela criança | `test_rf07_crianca_visualiza_somente_as_proprias_tarefas` |
| RF08 | Registro de conclusão por foto | `test_rf08_envio_de_evidencia_move_tarefa_para_revisao` |
| RF09 | Revisão da tarefa pelo Tutor | Testes de aprovação e rejeição em `RF07RF08RF09FluxoTarefaTests` |
| RF10 | Alertas e notificações | `RF10NotificacoesEPenalidadeTests.test_rf10_lembrete_cria_notificacao_para_crianca_com_acesso_proprio` |

## Regras de negócio e capacidades complementares

| Regra / capacidade | Evidência automatizada |
|---|---|
| Histórico deve permanecer íntegro após alteração do molde | `test_rn01_edicao_do_molde_nao_altera_tarefa_historica` |
| Exclusão do molde não pode apagar a instância histórica | `test_rn01_exclusao_do_molde_preserva_instancia_historica` |
| Envio da foto não concede pontos antes da revisão | `test_rf08_envio_de_evidencia_move_tarefa_para_revisao` |
| Aprovação concede pontos e registra revisor | `test_rf09_aprovacao_concede_pontos_e_registra_revisor` |
| Rejeição não concede pontos e permite novo envio | `test_rf09_rejeicao_nao_concede_pontos_e_permite_novo_envio` |
| Tarefa antiga não realizada aplica penalidade de 50%, arredondada para cima | `test_rn04_tarefa_antiga_nao_realizada_desconta_metade_arredondada_para_cima` |
| Penalidade não pode ser duplicada | `test_penalidade_nao_e_aplicada_duas_vezes` |
| XP histórico não é consumido no resgate de recompensa | `test_nivel_do_avatar_usa_xp_historico_e_nao_cai_ao_gastar_saldo` |
| Resgate sem saldo suficiente deve ser bloqueado | `test_resgate_sem_saldo_suficiente_e_bloqueado` |
| Cancelamento de resgate devolve pontos | `test_cancelamento_de_resgate_devolve_pontos` |
| XP de Skill é registrado uma única vez por tarefa/Skill | `test_aprovacao_de_skill_registra_xp_uma_unica_vez` |
| Níveis de Skills derivam do XP registrado | `test_painel_apresenta_skill_sem_inferir_valor_alem_do_xp_registrado` |
| Dias sem tarefas não quebram a sequência | `test_streak_ignora_dias_sem_tarefa` |
| Tarefa não realizada quebra a sequência | `test_tarefa_nao_realizada_interrompe_streak` |
| Primeira tarefa aprovada pode liberar conquista | `test_primeira_tarefa_aprovada_desbloqueia_conquista` |
| Relatório semanal consolida indicadores | `test_relatorio_semanal_consolida_indicadores_da_crianca` |
| Tutor não acessa dados de outra família | testes de edição de criança e relatório entre famílias diferentes |

## Requisitos não funcionais cobertos diretamente

| Código / aspecto | Evidência automatizada |
|---|---|
| PWA — Service Worker | `RNFPWATests.test_service_worker_tem_tipo_e_cabecalhos_esperados` |
| Captura de imagem — solicitação de câmera traseira | `test_rnf02_formulario_de_foto_solicita_camera_traseira` |
| Integridade e isolamento de dados | testes de escopo por família, snapshot histórico e idempotência |

## Observação metodológica

Os testes automatizados fornecem **evidência de validação técnica** do comportamento implementado. Para a defesa, a conclusão adequada é que os fluxos avaliados atenderam aos requisitos quando a suíte executar sem falhas no ambiente declarado.

Não é adequado afirmar, com base nesses testes, que:

- a aplicação é fácil de usar;
- a gamificação melhora o comportamento;
- as Skills medem desenvolvimento infantil;
- o sistema produz benefícios psicológicos ou educacionais.

Essas questões exigiriam métodos de pesquisa específicos e permanecem fora do escopo da validação técnica atual.

## Segurança, privacidade e LGPD — validação técnica

A atualização de segurança acrescenta **15 testes automatizados**, elevando a suíte automatizada para **54 testes** quando todos os módulos são descobertos pelo Django.

| Aspecto | Evidência automatizada |
|---|---|
| Cadastro exige ciência da Política de Privacidade | `PrivacyAndAccountSecurityTests.test_cadastro_exige_ciencia_da_politica` |
| Aceite registra data e versão da política | `test_aceite_registra_data_e_versao_vigente` |
| Exportação de dados é restrita ao Tutor e marcada `no-store` | `test_exportacao_e_privada_e_sem_cache` |
| Logout é uma operação POST, protegida contra acionamento por link externo | `test_logout_exige_post` |
| Operação sensível sem CSRF é rejeitada | `test_operacao_sensivel_sem_csrf_e_rejeitada` |
| Exclusão do único Tutor remove conta e família | `test_exclusao_do_unico_tutor_remove_familia_e_conta` |
| Em família compartilhada, conta removida é anonimizada sem apagar o histórico dos demais | `test_exclusao_em_familia_compartilhada_anonimiza_tutor` |
| Criança não acessa a Central de Privacidade administrativa | `test_crianca_nao_acessa_central_de_privacidade_do_tutor` |
| Evidência fotográfica exige autenticação | `PrivateEvidenceSecurityTests.test_evidencia_exige_autenticacao` |
| Tutor da família acessa evidência privada com cabeçalhos `no-store` | `test_tutor_da_familia_acessa_evidencia_sem_cache` |
| Criança acessa somente evidência vinculada ao próprio perfil | `test_crianca_acessa_somente_a_propria_evidencia` |
| Tutor de outra família recebe 404 ao tentar acessar uma evidência | `test_tutor_de_outra_familia_nao_acessa_evidencia` |
| `/media/` não expõe diretamente fotografias | `test_rota_media_publica_nao_entrega_evidencia` |
| Política de retenção remove foto antiga sem apagar histórico da tarefa | `test_retencao_remove_foto_antiga_sem_apagar_historico` |
| Upload é regravado em JPEG sem metadados EXIF/GPS | `test_formulario_regrava_imagem_em_jpeg_sem_metadados` |

### Comandos de segurança/privacidade

Remoção automática de evidências antigas, preservando o histórico da tarefa:

```powershell
python manage.py limpar_evidencias_antigas
```

Prazo personalizado:

```powershell
python manage.py limpar_evidencias_antigas --dias 180
```

Para produção, copie `.env.example`, utilize uma `DJANGO_SECRET_KEY` forte e configure `DJANGO_DEBUG=false`, hosts autorizados, origens CSRF e HTTPS.

> Estes testes validam controles técnicos do protótipo. Eles não substituem uma avaliação jurídica, definição formal de papéis de controlador/operador, registro de operações de tratamento, plano de resposta a incidentes ou demais obrigações organizacionais aplicáveis a uma disponibilização pública.
