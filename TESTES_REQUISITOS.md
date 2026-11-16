# Rastreabilidade de requisitos e testes — Rotina Conecta

Este documento relaciona o **Quadro 3 (RF01A–RF22)** e regras de negócio do RTS revisado aos testes disponíveis no repositório. **Os nomes dos métodos de teste conservam numeração histórica:** o prefixo `test_rf08_`, por exemplo, não significa que o método comprove o atual RF08. A correspondência correta é feita pelo **comportamento avaliado**.

**Classificação:** “teste identificado” significa que o método existe no código-fonte; **não** significa que foi executado com sucesso nesta revisão. “Inspeção/teste complementar” indica onde a validação ainda precisa ser ampliada.

## Executar a verificação

```powershell
pip install -r requirements.txt
python manage.py check
python manage.py test
python manage.py test usuarios tarefas gamificacao -v 2
```

Registre data, commit, ambiente, banco usado, total executado, falhas e erros antes de afirmar atendimento no RTS. Não se deve reutilizar sem nova execução a contagem histórica de 54 testes presente na versão antiga deste arquivo.

## Rastreabilidade funcional — IDs atuais

| RF atual | Comportamento | Evidência no código / teste identificado |
|---|---|---|
| RF01A | Cadastro/autenticação local | `usuarios/tests.py`: `test_rf01_tutor_autentica_com_usuario_e_senha`; cadastro: testes de privacidade |
| RF01B | Autenticação Google | Integração `django-allauth`; requer teste de integração com provedor |
| RF02 | Vínculos familiares | `test_rf02_convite_permite_segundo_responsavel_na_mesma_familia`, `test_rf02_convite_expirado_nao_pode_ser_usado` |
| RF03 | Perfil infantil e acesso opcional | `test_rf02_perfil_pode_existir_sem_login_proprio`, `test_rf02_formulario_cria_usuario_infantil_quando_acesso_proprio_ativo` |
| RF04 | Moldes de rotina | `test_rf03_molde_diario_gera_em_qualquer_dia`, `test_rf03_molde_semanal_respeita_dias_configurados`, testes RN01 |
| RF05 | Sugestões do catálogo | Implementação em `tarefas/views.py`; verificar cobertura dedicada de filtros e priorização |
| RF06 | Replicação | `test_rotina_pode_ser_replicada_para_todas_as_criancas_da_familia` |
| RF07 | Tarefa bônus | `test_rf04_tutor_cria_tarefa_bonus` |
| RF08 | Geração recorrente | `test_rf06_geracao_diaria_e_idempotente_e_copia_snapshot` |
| RF09 | Painel da criança | `test_rf07_crianca_visualiza_somente_as_proprias_tarefas` |
| RF10 | Fotografia e estado de revisão | `test_rf08_envio_de_evidencia_move_tarefa_para_revisao`; testes de mídia privada |
| RF11 | Aprovação/rejeição | `test_rf09_aprovacao_concede_pontos_e_registra_revisor`, `test_rf09_rejeicao_nao_concede_pontos_e_permite_novo_envio` |
| RF12 | Pontos e XP após aprovação | Testes de aprovação e `test_aprovacao_de_skill_registra_xp_uma_unica_vez` |
| RF13 | Encerramento e penalidade | `test_rn04_tarefa_antiga_nao_realizada_desconta_metade_arredondada_para_cima`, `test_penalidade_nao_e_aplicada_duas_vezes` |
| RF14 | Evolução das Skills | `test_intensidade_da_skill_mapeia_para_xp_previsto`, `test_painel_apresenta_skill_sem_inferir_valor_alem_do_xp_registrado` |
| RF15 | Gamificação | `test_nivel_do_avatar_usa_xp_historico_e_nao_cai_ao_gastar_saldo`, testes de sequência e conquistas |
| RF16 | Catálogo de recompensas | Implementação nos modelos e views de `gamificacao`; verificar CRUD diretamente |
| RF17 | Resgate | `test_resgate_sem_saldo_suficiente_e_bloqueado`, `test_cancelamento_de_resgate_devolve_pontos` |
| RF18 | Notificações internas | `test_rf10_lembrete_cria_notificacao_para_crianca_com_acesso_proprio` |
| RF19 | Relatório | `test_relatorio_semanal_consolida_indicadores_da_crianca`, `test_tutor_nao_acessa_relatorio_de_crianca_de_outra_familia` |
| RF20 | Interface inicial offline | `test_service_worker_tem_tipo_e_cabecalhos_esperados`; testar offline no navegador |
| RF21A | Aceite de privacidade | `test_cadastro_exige_ciencia_da_politica`, `test_aceite_registra_data_e_versao_vigente` |
| RF21B | Exportação | `test_exportacao_e_privada_e_sem_cache` |
| RF21C | Exclusão/anonimização | `test_exclusao_do_unico_tutor_remove_familia_e_conta`, `test_exclusao_em_familia_compartilhada_anonimiza_tutor` |
| RF21D | Retenção | `test_retencao_remove_foto_antiga_sem_apagar_historico`; comando `limpar_evidencias_antigas` |
| RF22 | Sugestões com IA | `test_extrair_json_aceita_cerca_markdown`, `test_normalizar_sugestoes_descarta_skill_invalida`, `test_sugestao_ia_sem_chave_falha_de_forma_controlada`; testar resposta real com provedor |

## Regras de negócio críticas (numeração do RTS revisado)

| Regra | Comportamento | Evidência identificada |
|---|---|---|
| RN01 | Alterações/exclusão do molde preservam instâncias | `test_rn01_edicao_do_molde_nao_altera_tarefa_historica`, `test_rn01_exclusao_do_molde_preserva_instancia_historica` |
| RN02 | Fotografia coloca em revisão; aprovação libera ganhos | Testes de envio, aprovação e rejeição |
| RN03 | Penalidade única de 50%, arredondamento para cima | Testes de desconto e de não duplicação |
| RN04 / RN17 | XP histórico não diminui; penalidade pode gerar saldo negativo | Teste de XP vs. resgate; conferir cenário específico de saldo negativo |
| RN05 | XP de Skill apenas após aprovação | `test_aprovacao_de_skill_registra_xp_uma_unica_vez` |
| RN06 | Resgate exige saldo; cancelamento devolve pontos | Testes de resgate sem saldo e de cancelamento |
| RN07 / RN08 | Isolamento familiar e evidência privada | Testes de permissões em `usuarios/tests.py` e `tarefas/test_security_privacy.py` |
| RN09 | Apagar fotografia antiga preserva o histórico | `test_retencao_remove_foto_antiga_sem_apagar_historico` |
| RN10 / RN11 | IA depende de confirmação e pode priorizar Skills | Testes de normalização/falha controlada; confirmar teste de aceite explícito e prioridades |
| RN12 / RN13 | Faixas de nível das Skills e do avatar | Inspecionar funções de cálculo e acrescentar testes para todos os limiares |
| RN14 | Dias sem tarefas não interrompem sequência | `test_streak_ignora_dias_sem_tarefa`, `test_tarefa_nao_realizada_interrompe_streak` |
| RN15 | Critérios de conquistas | `test_primeira_tarefa_aprovada_desbloqueia_conquista` |
| RN16 | Não penalizar tarefas em revisão pelo decurso do prazo | Conferir teste dedicado ao estado `Em revisão` |

## Requisitos não funcionais: evidência e lacunas

| RNF | Critério | Situação de verificação |
|---|---|---|
| RNF01 | Instalabilidade PWA | Manifesto/Service Worker identificados; testar instalação em navegador compatível |
| RNF02 | Responsividade ≥360 px | Requer teste visual em dispositivos/viewport; não é demonstrado apenas pelo CSS |
| RNF03 | Proteção de cache privado | Testes de evidência e exportação sem cache; auditar demais páginas autenticadas |
| RNF04 | Remoção de EXIF/GPS | `test_formulario_regrava_imagem_em_jpeg_sem_metadados`; ampliar com arquivo de entrada contendo EXIF/GPS |
| RNF05 | Segredos por variáveis de ambiente | Inspecionar `.env.example` e `config/settings.py`; não expor segredos reais |
| RNF06 | HTTPS em produção | Configuração em Django não substitui verificação TLS em implantação real |
| RNF07 | Módulos separados por responsabilidade | Inspeção de `usuarios`, `tarefas`, `gamificacao` |
| RNF08 | Regras reutilizadas em serviços | Inspeção de `tarefas/services.py` e `gamificacao/services.py`; conferir todas as rotas mutáveis |
| RNF09 | Testes automatizados de fluxos críticos | Métodos identificados; executar suíte e registrar resultados reais |

## Processos por data: atenção à terminologia

- `processar_rotinas()` é acionado em determinados acessos à aplicação e pode ser executado pelo comando `gerar_tarefas_diarias`.
- `limpar_evidencias_antigas` remove arquivos elegíveis e preserva os registros, mas depende de execução administrativa ou agendamento de infraestrutura.
- A existência dos comandos não comprova que há **agendador externo em execução** nem que o processamento ocorre à meia-noite quando não há acessos.

## Limites das conclusões

A análise do código e a presença de testes constituem evidência de implementação, não resultado de execução nem avaliação com famílias. Não permitem afirmar melhora de comportamento, desenvolvimento de competências, usabilidade ou conformidade jurídica integral à LGPD. Documente separadamente eventuais testes manuais, navegadores, resoluções, ambiente de banco de dados e resultados obtidos.
