# ChargeGrid Intelligence — Responsabilidades do Projeto

> Referência central de ownership para todos os integrantes.  
> Atualizado pelo líder do projeto (Pedro) a cada sprint.  
> EV Challenge 2026 — GoodWe / FIAP | 

---

## Equipe e Etiquetas do Trello

| Etiqueta | Integrante | RM | Função |
|----------|------------|----|--------|
| 🟣 Sem etiqueta | Pedro Sampaio Mochnacs Arruda | RM 573522 | Líder, coordenador e integrador final |
| 🔵 Azul | Raul Sampaio Mochnacs Arruda | RM 573523 | Backend — banco de dados, autenticação e pagamentos |
| 🟡 Amarela | Lucas Garcia de Britto | RM 571768 | IA e Chatbot — RAG, LLM e integração de dados |
| 🔴 Vermelha | Luan de Araujo Carneiro | RM 573691 | Frontend e UI — dashboard, protótipos e telas |
| 🟢 Verde | Kevin Rodrigues de Melo | RM 571777 | Dados e ML — análise comercial e IA preditiva |

> Cards com duas etiquetas = tarefa colaborativa entre dois membros.  
> Cada membro é responsável pela sua parte específica dentro da tarefa conjunta.

---

## Arquitetura da Solução Final

```
ev_chargegrid.py  (Motor principal — base de tudo)
│
├── [🔵 Raul]      Banco de Dados e Autenticação
├── [🔵 Raul]      Gateway de Pagamentos (Mercado Pago Sandbox)
├── [🟢 Kevin]     IA Preditiva — modelo ML (.pkl)
└──               OCPP 1.6J, DLB ✅ Concluído

Chatbot IA  (ChargeGrid_Intelligence_Sprint2.ipynb → Sprint 3)
├── [🟡 Lucas]     Pipeline RAG com dados reais da planilha Excel
└── [🟡 Lucas]     Integração com dados em tempo real do ev_chargegrid.py

Interface Visual
├── [🔴 Luan]      Dashboard de Monitoramento em Tempo Real
└── [🔴 Luan]      Protótipos de Tela — Totem + App + QR Pix

Entrega Final
└── [Pedro]        Integração, revisão, vídeo e apresentação
```

---

## Tarefas Colaborativas (dois membros)

Estas três tarefas do Kanban são de responsabilidade compartilhada.  
Cada membro executa uma frente diferente — a integração final é feita pelo Pedro.

---

### 🔵🔴 Autenticação e Criptografia — Raul + Luan
**Status:** Em andamento

A autenticação precisa de backend e frontend ao mesmo tempo — não faz sentido um sem o outro.

**Raul faz (backend):**
- Lógica de autenticação no `ev_chargegrid.py` — verificação de placa/ID antes de liberar `iniciar_sessao()`
- Criptografia dos dados do usuário (hash da placa ou token de sessão)
- Retornar `True/False` ou token para o frontend consumir

**Luan faz (frontend):**
- Tela de login/autenticação no Totem e no App
- Fluxo de entrada do usuário: digita placa → sistema valida → libera carregador
- Feedback visual de autenticação (aprovado / negado / aguardando)

**Ponto de encontro:** A função `iniciar_sessao()` do Raul precisa receber o ID validado que vem da tela do Luan.  
**Entregam juntos para Pedro:** módulo de autenticação funcional de ponta a ponta (backend + tela).

---

### 🔵🟡 Integração com Base de Dados — Raul + Lucas
**Status:** Em andamento

O banco de dados serve a dois módulos: o motor Python do Raul e o chatbot do Lucas.  
A divisão evita que um bloqueie o outro.

**Raul faz (backend):**
- Criar o schema do banco (tabela de sessões, usuários, consumo, receita)
- Substituir a lista `estacoes[]` do `ev_chargegrid.py` por queries INSERT/UPDATE/SELECT
- Exportar os dados em um formato que o chatbot consiga consumir (JSON ou consulta direta)

**Lucas faz (IA/chatbot):**
- Adaptar o pipeline RAG para ler os dados do banco ou do arquivo exportado pelo Raul
- Garantir que o chatbot consiga responder sobre dados reais (ex: "qual o faturamento de hoje?")
- Não depender mais dos 12 documentos estáticos do Sprint 2

**Ponto de encontro:** O formato de exportação do Raul (JSON ou tabela) precisa ser combinado com o Lucas antes de cada um começar a parte dele.  
**Entregam juntos para Pedro:** banco populado com dados reais + chatbot lendo esses dados.

---

### 🟢🟡 Evolução do Chatbot IA — RAG com Base de Dados (Excel) — Kevin + Lucas
**Status:** Em andamento

O Kevin domina os dados e o modelo analítico; o Lucas domina o pipeline do chatbot. Juntos evoluem o RAG para além dos documentos fixos.

**Kevin faz (dados/ML):**
- Processar e estruturar a planilha `Trabalho_Analise_Comercial_SP2.xlsx` para alimentar o RAG
- Preparar os dados em um formato indexável (chunks de texto, CSV limpo ou JSON)
- Identificar quais métricas e informações da planilha são mais relevantes para o chatbot responder

**Lucas faz (IA/chatbot):**
- Substituir os 12 documentos estáticos do `SPRINT 2` pela base de dados preparada pelo Kevin
- Atualizar a função `buscar_contexto()` para buscar nos dados reais, não em strings fixas
- Rodar os casos de teste e gerar o `resultados_testes_sprint3.json`

**Ponto de encontro:** Kevin entrega os dados formatados → Lucas indexa no pipeline RAG.  
**Entregam juntos para Pedro:** chatbot respondendo com dados da planilha real, não dados fictícios.

---

## Tarefas Individuais

---

### 🔵 Raul — Módulo de Faturamento + Gateway de Pagamentos
**Status:** Para fazer  
**Após concluir:** Autenticação e Integração com BD

O sistema hoje só imprime o recibo no terminal. O objetivo é disparar uma cobrança real via API.

**O que fazer:**
- Na função `encerrar_sessao()` do `ev_chargegrid.py`, substituir o `print()` do recibo por uma chamada à API do **Mercado Pago Sandbox**
- Enviar: valor da sessão, método de pagamento (PIX/Cartão/QRCode) e ID do usuário
- Receber confirmação de pagamento antes de liberar a vaga do posto
- Registrar o resultado da cobrança no banco de dados

**Entrega para Pedro:** `ev_chargegrid.py` com gateway integrado + log ou screenshot de uma cobrança de teste no Sandbox.

---

### 🔴 Luan — Dashboard de Monitoramento em Tempo Real
**Status:** Para fazer  
**Pode iniciar:** Em paralelo com a autenticação

O dashboard é a interface do operador do posto — ele precisa ver o status de todas as estações, potência e receita sem abrir o terminal.

**O que fazer:**
- Criar dashboard em HTML/React (ou Figma navegável, caso o prazo aperte)
- Exibir os dados que `painel_operacional()` já calcula: status de cada estação (livre/ocupada), potência ativa, kWh consumidos, receita acumulada
- Conectar com dados reais ou simular com os dados do `ev_chargegrid.py` enquanto a API do Raul não estiver pronta
- Atualização em tempo real (polling simples ou websocket, conforme o tempo permitir)

**Entrega para Pedro:** Dashboard funcional com dados visíveis + protótipo ou link navegável.

---

### 🔴 Luan — Protótipos de Tela — Totem + App + QR Pix
**Status:** Para fazer  
**Pode iniciar:** Agora, é independente

Esta tarefa é paralela e não depende do backend estar pronto.

**O que fazer:**
- Criar os protótipos das telas que o usuário final vê no posto:
  - **Totem:** tela de boas-vindas → autenticação por placa → seleção de carregador → acompanhamento da sessão → encerramento com QR para pagamento
  - **App:** versão mobile do mesmo fluxo (pode ser Figma)
  - **QR Pix:** tela de confirmação de pagamento gerada ao encerrar a sessão
- As telas da autenticação aqui devem ser consistentes com o que o Raul está implementando no backend

**Entrega para Pedro:** Protótipos navegáveis (Figma, HTML ou similar) cobrindo os três fluxos.

---

### 🟢 Kevin — IA Preditiva Real (Substituição do Dicionário por ML)
**Status:** Backlog  
**Após concluir:** Parte do RAG com Lucas

O sistema hoje usa um dicionário fixo para prever demanda por hora. Kevin vai substituir por um modelo treinado com dados reais.

**O que fazer:**
- Treinar um modelo de regressão simples (`scikit-learn`) usando os dados da planilha SP2: hora do dia → fator de demanda previsto
- Exportar o modelo como `modelo_demanda.pkl` com `joblib`
- O Pedro integra substituindo a função no `ev_chargegrid.py`:

```python
import joblib
modelo_ml = joblib.load("modelo_demanda.pkl")

def ia_prever_demanda(hora: int) -> float:
    return float(modelo_ml.predict([[hora]])[0])
```

**Entrega para Pedro:** Notebook de treinamento + arquivo `modelo_demanda.pkl` + breve análise dos resultados (gráfico de demanda prevista x real).

---

### 🟡 Lucas — Chatbot: Integração com Dados em Tempo Real
**Status:** Backlog  
**Após concluir:** RAG com Kevin + banco do Raul estar funcional

Esta é a etapa final do chatbot — depois que o RAG com Excel e o banco de dados estiverem prontos.

**O que fazer:**
- Conectar o chatbot ao banco de dados do Raul para responder sobre o estado atual do sistema em tempo real
- Exemplos de perguntas que devem funcionar: *"Qual carregador está ocupado agora?"*, *"Qual o faturamento de hoje?"*, *"Tem algum carregador em manutenção?"*
- Atualizar o `SYSTEM_PROMPT` se necessário para refletir os dados reais

**Entrega para Pedro:** Chatbot respondendo perguntas com dados do banco em tempo real + JSON de testes atualizado.

---

### Pedro — Apresentação Final do Projeto
**Status:** Backlog  
**Inicia:** Quando os demais módulos estiverem integrados

**O que fazer:**
- Integrar todos os módulos recebidos dos membros no repositório final
- Gravar o vídeo de demonstração da solução completa (substituindo o vídeo parcial atual)
- Consolidar slides de apresentação cobrindo: problema, solução, arquitetura, demonstração, resultados
- Submeter o projeto conforme os critérios do EV Challenge 2026

---

## Status Consolidado

| Card | Responsáveis | Tipo | Status |
|------|-------------|------|--------|
| Sistema Base Python | Time | Conjunto | ✅ Concluído |
| DLB — Balanceamento Dinâmico | Time | Conjunto | ✅ Concluído |
| Simulação Protocolo OCPP | Time | Conjunto | ✅ Concluído |
| Análise Comercial (planilha SP2) | Kevin | Individual | ✅ Concluído |
| Documentação técnica | Pedro | Individual | ✅ Concluído |
| Vídeo de demonstração parcial | Pedro | Individual | ✅ Concluído |
| 🔵🔴 Autenticação e Criptografia | Raul + Luan | Colaborativa | 🔄 Em andamento |
| 🔵🟡 Integração com Base de Dados | Raul + Lucas | Colaborativa | 🔄 Em andamento |
| 🟢🟡 Chatbot RAG com Excel | Kevin + Lucas | Colaborativa | 🔄 Em andamento |
| 🔵 Faturamento + Gateway | Raul | Individual | 📋 Para fazer |
| 🔴 Dashboard em Tempo Real | Luan | Individual | 📋 Para fazer |
| 🔴 Protótipos Totem + App + QR | Luan | Individual | 📋 Para fazer |
| 🟢 IA Preditiva Real (ML) | Kevin | Individual | ⏳ Backlog |
| 🟡 Chatbot com Dados em Tempo Real | Lucas | Individual | ⏳ Backlog |
| Apresentação Final | Pedro | Individual | ⏳ Backlog |

---

## Regra de Entrega 

Cada integrante entrega ao Pedro **antes do prazo final**:

| O que entregar | Formato |
|----------------|---------|
| O arquivo produzido | `.py`, `.ipynb`, `.pkl`, `.html`, `.fig` ou similar |
| Evidência de funcionamento | Print, vídeo curto (30s), log ou screenshot |
| Instruções de integração | O que o Pedro precisa saber para encaixar sem quebrar o que já existe |

> Tarefa colaborativa = os dois membros entregam juntos, já integrados entre si.  
> Pedro não integra partes separadas de uma tarefa colaborativa — ela chega pronta.

---

> *Atualizar este documento sempre que um card mudar de coluna no Trello.*  
> *Versão: Sprint 3 — 14 dias restantes*
