# ChargeGrid Intelligence — Documento de Responsabilidades do Projeto

> Referência central de ownership para todos os integrantes.  
> Atualizado pelo líder do projeto (M1) a cada sprint.  
> EV Challenge 2026 — GoodWe / FIAP

---

## Equipe

| Sigla | Integrante | RM | Função no Projeto |
|-------|------------|----|-------------------|
| M1 | Pedro Sampaio Mochnacs Arruda | RM 573522 | Líder, coordenador e integrador final |
| M2 | Luan de Araujo Carneiro | RM 573691 | Backend — banco de dados, autenticação e pagamentos |
| M3 | Raul Sampaio Mochnacs Arruda | RM 573523 | IA e Chatbot — RAG, LLM e integração de dados |
| M4 | Lucas Garcia de Britto | RM 571768 | Frontend e UI — dashboard, protótipos e telas |
| M5 | Kevin Rodrigues de Melo | RM 571777 | Dados e ML — análise comercial e IA preditiva |

> Preencha ou ajuste a coluna "Integrante" conforme a etiqueta de cor de cada membro no Trello.

---

## Visão Geral do Projeto

O ChargeGrid Intelligence é uma plataforma de gestão comercial de eletropostos para alto fluxo.  
A solução final integra cinco componentes desenvolvidos em paralelo pelos membros da equipe:

```
Motor Backend (Python)
    ├── Banco de Dados e Autenticação    → M2
    ├── Gateway de Pagamentos            → M2
    ├── Tarifação Dinâmica por IA/ML     → M5
    └── Protocolo OCPP 1.6J              ✓ Concluído

Chatbot IA (Ollama / LangChain)
    ├── RAG com base de dados Excel      → M3
    └── Integração com dados em tempo real → M3

Interface Visual
    ├── Dashboard de Monitoramento       → M4
    └── Protótipos (Totem + App + QR)   → M4

Coordenação e Entrega Final             → M1
```

---

## Responsabilidades por Integrante

### M1 —  Integrador (Pedro)

**Função:** Coordenar as entregas, integrar os módulos desenvolvidos pelos membros e consolidar o material final para apresentação e submissão.

| # | Tarefa | Status | Observação |
|---|--------|--------|------------|
| 1 | Coordenação geral e acompanhamento do Kanban | Contínuo | Atualizações semanais no Trello |
| 2 | Revisão e integração dos módulos entregues | Contínuo | Verificar compatibilidade entre partes |
| 3 | Atualização dos READMEs do repositório | Contínuo | Este documento é responsabilidade do M1 |
| 4 | Apresentação Final do Projeto | Backlog | Consolidar vídeo, slides e demo integrada |

**O que M1 recebe dos outros membros para integrar:**
- M2: módulo de autenticação funcional + script de banco de dados + integração gateway
- M3: chatbot atualizado com RAG conectado à planilha e dados do sistema
- M4: dashboard funcional + protótipos navegáveis
- M5: modelo ML serializado (.pkl) + análise comercial final

---

### M2 — Backend (Raul)

**Função:** Implementar a camada de persistência de dados, autenticação segura e integração com gateway de pagamento no `ev_chargegrid.py`.

| # | Tarefa | Status | Ponto de integração no código |
|---|--------|--------|-------------------------------|
| 1 | Módulo de Autenticação e Criptografia | Em andamento | Novo módulo — autenticar usuário antes de `iniciar_sessao()` |
| 2 | Integração com Base de Dados | Em andamento | Substituir lista `estacoes[]` por queries de INSERT/UPDATE |
| 3 | Módulo de Faturamento + Gateway de Pagamentos | Para fazer | Substituir `print()` do recibo por chamada à API do Mercado Pago Sandbox |

**Entrega para M1:**
- Arquivo `ev_chargegrid.py` atualizado com os três módulos integrados
- Script SQL ou schema de banco de dados utilizado
- Evidência de teste do gateway (screenshot ou log da chamada sandbox)

**Dependências:**
- M5 precisa que o banco de dados exista para persistir o histórico de sessões que alimentará o modelo ML

---

### M3 — IA e Chatbot (Lucas)

**Função:** Evoluir o chatbot do Sprint 2 para consumir dados reais do sistema e responder perguntas de negócio em tempo real.

| # | Tarefa | Status | Observação |
|---|--------|--------|------------|
| 1 | Evolução do Chatbot IA: RAG com Base de Dados Excel | Em andamento | Substituir documentos estáticos pela planilha `Trabalho_Analise_Comercial_SP2.xlsx` |
| 2 | Integração do Chatbot com Dados em Tempo Real | Backlog | Consumir logs/saídas do `ev_chargegrid.py` via M2 |

> **Atenção:** Os cards "Evolução do Chatbot RAG" e "Integração com Dados em Tempo Real" são etapas sequenciais da mesma entrega — não trabalhos diferentes. O segundo só começa depois que M2 tiver o banco de dados funcionando.

**Entrega para M1:**
- Notebook atualizado com RAG conectado à planilha Excel
- Versão final do chatbot respondendo perguntas com dados reais do sistema
- JSON de resultados de testes atualizado (`resultados_testes_sprint3.json`)

**Dependências:**
- Etapa 2 depende do banco de dados do M2 estar funcional

---

### M4 — Frontend e UI (Luan)

**Função:** Criar a interface visual do sistema — dashboard operacional e protótipos das telas de atendimento ao usuário final.

| # | Tarefa | Status | Observação |
|---|--------|--------|------------|
| 1 | Dashboard de Monitoramento em Tempo Real | Para fazer | Consumir dados da função `painel_operacional()` do `ev_chargegrid.py` |
| 2 | Protótipos de Tela — Totem + App + QR Pix | Para fazer | Interface do usuário final no posto de recarga |

**Entrega para M1:**
- Dashboard funcional (HTML/React ou equivalente) com dados do sistema
- Protótipos navegáveis das telas (Figma, HTML ou similar)
- Evidência de que o dashboard consome dados reais ou simulados do backend

**Dependências:**
- Dashboard depende da função `painel_operacional()` do M2 expor dados via API ou exportação
- Protótipos de tela são independentes e podem ser desenvolvidos em paralelo agora

---

### M5 — Dados e ML (Kevin)

**Função:** Elevar a inteligência do sistema com análise comercial real e modelo de IA preditiva treinado com os dados históricos do projeto.

| # | Tarefa | Status | Observação |
|---|--------|--------|------------|
| 1 | Análise Comercial Base (planilha SP2) | Concluído ✓ | Integrada ao sistema como base de dados |
| 2 | IA Preditiva Real — substituir dicionário por modelo ML | Backlog | Treinar com os dados da planilha; exportar como `.pkl` |

**Onde integrar no código:**  
Substituir `DEMANDA_PREVISTA_POR_HORA` e a função `ia_prever_demanda()` em `ev_chargegrid.py` por carregamento do modelo serializado:
```python
import joblib
modelo_ml = joblib.load("modelo_demanda.pkl")

def ia_prever_demanda(hora: int) -> float:
    return modelo_ml.predict([[hora]])[0]
```

**Entrega para M1:**
- Notebook de treinamento do modelo (scikit-learn)
- Arquivo `modelo_demanda.pkl` pronto para importação no `ev_chargegrid.py`
- Análise comercial final consolidada (métricas de faturamento, pico de demanda, ROI estimado)

**Dependências:**
- Quanto mais dados reais o M2 tiver no banco, melhor o modelo. Para o prazo atual, treinar com os dados da planilha SP2 é suficiente.

---

## Status Consolidado do Kanban

| Card | Responsável | Status |
|------|-------------|--------|
| Sistema Base Python (`ev_chargegrid.py`) | M1 + Time | ✅ Concluído |
| DLB — Balanceamento Dinâmico de Carga | M1 + Time | ✅ Concluído |
| Simulação Protocolo OCPP 1.6J | M1 + Time | ✅ Concluído |
| Análise Comercial Base (planilha SP2) | M5 | ✅ Concluído |
| Documentação técnica | M1 | ✅ Concluído |
| Vídeo de demonstração parcial | M1 | ✅ Concluído |
| Módulo de Autenticação e Criptografia | M2 | 🔄 Em andamento |
| Integração com Base de Dados | M2 | 🔄 Em andamento |
| Evolução do Chatbot IA — RAG + Excel | M3 | 🔄 Em andamento |
| Módulo de Faturamento + Gateway | M2 | 📋 Para fazer |
| Dashboard de Monitoramento em Tempo Real | M4 | 📋 Para fazer |
| Protótipos de Tela — Totem + App + QR Pix | M4 | 📋 Para fazer |
| IA Preditiva Real (ML) | M5 | ⏳ Backlog |
| Chatbot: Integração com Dados em Tempo Real | M3 | ⏳ Backlog (etapa 2 do RAG) |
| Apresentação Final do Projeto | M1 | ⏳ Backlog |

---

## Regra de Entrega para o M1

Cada integrante entrega ao M1:

1. **O arquivo modificado ou criado** (código, notebook, protótipo, modelo)
2. **Uma evidência de funcionamento** (print, vídeo curto, log, screenshot)
3. **O que o próximo módulo precisa saber** para integrar sem quebrar o que já existe

Sem esses três itens, a entrega não está pronta para integração.

---

> *Este documento deve ser atualizado pelo M1 sempre que um card mudar de status no Trello.*  
> *Versão atual: Sprint 3 — 14 dias restantes*
