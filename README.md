# ChargeGrid Intelligence — Responsabilidades do Projeto

> Referência central de ownership para todos os integrantes.
> Atualizado pelo líder do projeto (Pedro) a cada sprint.
> EV Challenge 2026 — GoodWe / FIAP

Integração com dados reais
**Prazo final de entrega:** meados de agosto de 2026. Quanto antes estiver pronto, melhor — os prazos abaixo são o limite máximo de cada entrega, não a meta.

---

## Nomenclatura simplificada no banco

> A coluna de usuário na tabela `sessoes` se chama simplesmente **`usuario`**. Os dados já chegam mascarados por padrão (placa parcialmente oculta, por LGPD) antes de serem gravados — então quem for escrever uma query direta fora das 4 funções prontas não precisa pensar em máscara nenhuma, só usa `usuario` normalmente.

---

## Equipe e Etiquetas do Trello

| Etiqueta | Integrante | RM | Função |
|----------|------------|----|--------|
| ⚪ Sem etiqueta | Pedro Sampaio Mochnacs Arruda | RM 573522 | Líder, coordenador e integrador final |
| 🔵 Azul | Raul Sampaio Mochnacs Arruda | RM 573523 | Backend — banco de dados, autenticação e pagamentos |
| 🟡 Amarela | Lucas Garcia de Britto | RM 571768 | IA e Chatbot — RAG, LLM e integração de dados |
| 🔴 Vermelha | Luan de Araujo Carneiro | RM 573691 | Frontend e UI — dashboard, protótipos e telas |
| 🟢 Verde | Kevin Rodrigues de Melo | RM 571777 | Dados e ML — análise comercial e IA preditiva |

> **Cards com duas etiquetas = tarefa colaborativa.** A integração entre as duas partes é responsabilidade dos próprios membros — Pedro só recebe quando estiver funcionando de ponta a ponta.

---

## Arquitetura da Solução Final

```
ev_chargegrid.py  ← Motor principal do sistema (CONCLUÍDO — Raul)
│
├── [🔵 Raul]  Banco de Dados SQLite (chargegrid.db) — tabelas usuarios + sessoes ✅
├── [🔵 Raul]  Autenticação por hash SHA-256 + mascaramento de placa (LGPD) ✅
├── [🔵 Raul]  Gateway de Pagamento Sandbox — simulado por padrão, com opção de
│              ativar API real do Mercado Pago (USAR_API_REAL_MERCADOPAGO) ✅
├── [🔵 Raul]  4 funções de leitura prontas — ver seção própria abaixo ✅
├── [🟢 Kevin] IA Preditiva — modelo_demanda.pkl (em treinamento, prazo 07/07)
└──            OCPP 1.6J + DLB ✅ Concluído

chargegrid.db  ← já existe e está sendo populado em tempo real
├── tabela `usuarios`  (hash_usuario, nome, status)
└── tabela `sessoes`   (id, id_estacao, usuario, data_sessao,
                         hora_inicio, kwh_consumidos, valor_sessao,
                         metodo_pagamento, status_pagamento, ativa)

ChargeGrid_Sprint3.ipynb  ← Chatbot evoluído (Lucas)
├── [🟢➝🟡 Kevin → Lucas]  dados_rag.json substitui os 12 documentos fixos do Sprint 2
└── [🟡 Lucas]             Roteador de tempo real conectado nas 4 funções do Raul

Interface Visual
├── [🔴 Luan]  dashboard.py com Streamlit, lendo as 4 funções do Raul
└── [🔴 Luan]  Protótipos de Tela — Totem + App + QR Pix

Entrega Final
└── [Pedro]  Integra o modelo do Kevin (07/07) → integração geral (25/07) →
             vídeo, slides e submissão (até meados de agosto)
```

---

## Entendendo os Componentes Principais

### O que é o banco de dados e por que não é o Excel

A planilha `Trabalho_Analise_Comercial_SP2.xlsx` é um arquivo de análise histórica — dados preenchidos manualmente para estudar o comportamento do sistema. Ela é estática: alguém abre, lê, fecha. Não muda sozinha enquanto o sistema roda.

O banco de dados é diferente: é onde o `ev_chargegrid.py` grava automaticamente cada evento em tempo real — toda sessão que começa, todo kWh consumido, todo pagamento processado. É o "diário de bordo" automático do sistema.

Usamos **SQLite** — um banco que fica em um único arquivo `.db` na pasta do projeto, sem precisar instalar servidor nenhum. O Python já tem suporte nativo via `import sqlite3`. Este é o schema real, já implementado e funcionando:

```python
# Como o banco é criado (já implementado em ev_chargegrid.py, função inicializar_banco())
import sqlite3

conn = sqlite3.connect("chargegrid.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        hash_usuario TEXT PRIMARY KEY,
        nome TEXT,
        status TEXT DEFAULT 'ATIVO'
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessoes (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        id_estacao           INTEGER,
        usuario              TEXT,
        data_sessao          TEXT,
        hora_inicio          INTEGER,
        kwh_consumidos       REAL DEFAULT 0.0,
        valor_sessao         REAL DEFAULT 0.0,
        metodo_pagamento     TEXT,
        status_pagamento     TEXT DEFAULT 'PENDENTE',
        ativa                INTEGER DEFAULT 1
    )
""")
conn.commit()
```

Note as diferenças em relação ao esboço original deste documento: a coluna de usuário se chama `usuario` (simplificado de propósito — os dados já vêm mascarados por padrão, então o nome da coluna não precisa carregar isso), existe uma tabela `usuarios` separada para autenticação, e o campo `ativa` substitui o antigo `encerrada` com lógica invertida (1 = em andamento, 0 = encerrada). O campo `data_sessao` foi adicionado para permitir perguntas como "faturamento de hoje".

**Resumo das responsabilidades de cada fonte de dados:**

| Fonte | O que contém | Quem usa | Para quê |
|-------|-------------|----------|----------|
| `Trabalho_Analise_Comercial_SP2.xlsx` | Dados históricos de análise | Kevin, Lucas | Treinar o modelo ML e enriquecer o RAG |
| `chargegrid.db` | Sessões em tempo real geradas pelo sistema | Raul, Lucas, Kevin, Luan | Tudo que precisa refletir o estado atual do sistema |

Por que duas fontes? O SQLite responde o agora — vaga livre, consumo ativo, status do carregador. O Excel responde o histórico — receita por mês, pico de demanda, ROI. Separar as camadas operacional e estratégica é o que transforma o chatbot em ferramenta de decisão real, não só um painel de texto.

---

### As 4 funções de leitura prontas (API interna do Raul)

Ninguém além do Raul precisa escrever SQL ou tocar no motor principal. Estas 4 funções já vêm prontas em `ev_chargegrid.py` e qualquer um pode importar direto:

```python
from ev_chargegrid import (
    listar_sessoes_ativas,
    obter_status_estacoes,
    obter_faturamento_dia,
    contar_sessoes_dia
)
```

| Função | O que retorna | Quem usa |
|--------|----------------|----------|
| `listar_sessoes_ativas()` | Lista de sessões em andamento agora (estação, usuário, kWh, valor, pagamento) | Lucas (chatbot), Luan (dashboard) |
| `obter_status_estacoes()` | Status Livre/Ocupada de todas as 10 estações | Luan (dashboard), Lucas (chatbot) |
| `obter_faturamento_dia(data=None)` | Soma das sessões pagas no dia informado (hoje, por padrão) | Lucas (chatbot), Luan (dashboard) |
| `contar_sessoes_dia(data=None)` | Quantidade de sessões iniciadas no dia informado | Lucas (chatbot) |

Funções auxiliares também disponíveis: `cadastrar_usuario(placa, nome)` para registrar uma placa nova em tempo real (útil na demonstração), e `confirmar_pagamento(id_sessao_db)` para finalizar uma cobrança sem depender de input de terminal — pensada para ser chamada por um botão do dashboard ou totem no futuro.

---

### O que são os 12 documentos estáticos do Sprint 2

No notebook do Sprint 2, o chatbot funciona assim:

```python
documentos = [
    "CP-03 gerou 312 kWh e R$ 280,80 de receita em maio.",
    "CP-02 gerou 241 kWh e R$ 216,90 de receita em maio.",
    # ... mais 10 frases fixas
]
```

São 12 frases digitadas na mão que simulam o que o sistema "sabe". O problema: são dados inventados e nunca mudam.

**No Sprint 3, essas 12 frases são substituídas por `dados_rag.json`** — o arquivo que o Kevin entrega (prazo 24/06) processando a planilha SP2 em texto estruturado. O Lucas substitui a lista fixa por esse arquivo (prazo 11/07), e o chatbot passa a responder com dados verdadeiros, tanto históricos (via `dados_rag.json`) quanto em tempo real (via as 4 funções do Raul).

---

### Como funciona o modelo de IA preditiva (tarefa do Kevin)

Hoje existe este dicionário fixo em `ev_chargegrid.py`:

```python
DEMANDA_PREVISTA_POR_HORA = {
     0: 0.05,  1: 0.03,  2: 0.03,  3: 0.03,
     6: 0.20,  7: 0.45,  8: 0.70,  9: 0.80,
    12: 1.00, 13: 0.85, 18: 1.00, 19: 1.00,
    ...
}
```

Esses números foram digitados na intuição de quem escreveu o código. **scikit-learn** aprende esse padrão a partir de dados reais em vez de intuição. O Kevin treina o modelo com os dados de horário da planilha SP2 (prazo 07/07), exporta como `modelo_demanda.pkl` com `joblib`, e o Pedro substitui o dicionário fixo (mesmo prazo, 07/07):

```python
import joblib
modelo_ml = joblib.load("modelo_demanda.pkl")

def ia_prever_demanda(hora: int) -> float:
    return float(modelo_ml.predict([[hora]])[0])
```

---

## Entregas por Integrante — Sprint 3 (com prazos)

### 🔵 Raul — Sem tarefas pendentes ✅

Todas as entregas obrigatórias do Raul já foram concluídas: banco de dados, autenticação, gateway de pagamento e as 4 funções de leitura. Ele não tem nenhum prazo no quadro abaixo — o trabalho dele encerrou nesta etapa.

**Papel agora:** apoio sob demanda. Se Lucas ou Luan travarem por causa de query ou comportamento do banco, Raul resolve rápido, mas isso não é uma entrega com prazo.

**Bônus opcional (não é tarefa, é melhoria se sobrar tempo) — Mercado Pago real**
O código já está preparado para isso, se o Raul quiser fazer antes de 25/07: criar conta gratuita em developers.mercadopago.com, pegar o Access Token de teste (`TEST-...`, gratuito), e trocar o token mock pelo real ligando `USAR_API_REAL_MERCADOPAGO = True`. O código já cai no fallback simulado automaticamente se isso não for feito. Não é bloqueante pra entrega final.

---

### 🟢 Kevin

**Entrega 1 — `dados_rag.json` | Prazo: 24/06**
Extrai da planilha SP2 as métricas principais (receita por carregador, sessões por horário, ticket médio, pico de demanda) e transforma em texto estruturado, no formato já combinado com o Lucas. Junto com o arquivo, envia um exemplo da estrutura ou uma explicação curta dos campos, para o Lucas não precisar adivinhar o formato.

**Entrega 2 — `requirements.txt` | Prazo: 24/06**
Lista as bibliotecas necessárias para rodar os artefatos do Kevin (processamento da planilha, notebook de treino, geração do modelo). Mínimo esperado: `scikit-learn`, `joblib`, `pandas`, `matplotlib`. As dependências do projeto completo serão consolidadas por Pedro na integração final.

**Entrega 3 — `modelo_demanda.pkl` + notebook de treinamento + gráfico comparativo | Prazo: 07/07**
Depois das Entregas 1 e 2, treina o modelo de regressão com os dados de horário da planilha, exporta com `joblib`, e inclui um gráfico comparando a previsão do modelo com o dicionário original.

---

### 🟡 Lucas

**Frente 1 — Roteador de tempo real no `buscar_contexto()` | Prazo: 30/06**
Constrói um roteador simples por palavra-chave dentro do `buscar_contexto()`: perguntas com "agora", "hoje", "livre", "ocupado", "faturamento", "ativa" chamam as 4 funções do Raul; perguntas históricas como "receita de maio", "pico de demanda", "ticket médio" vão pro RAG com os dados do Kevin. Pode começar já — não depende de mais nada.

**Frente 2 — Substituir os 12 documentos pelo `dados_rag.json` | Prazo: 11/07**
Quando o Kevin entregar o `dados_rag.json` (24/06), substitui a lista fixa do Sprint 2 pelos dados reais. Atualiza o `SYSTEM_PROMPT` se necessário.

**Entrega final — `ChargeGrid_Sprint3.ipynb` + `resultados_testes_sprint3.json` | Prazo: 21/07**
Notebook com as duas frentes funcionando juntas. O JSON de testes precisa responder com dados reais pelo menos: "Qual carregador está ocupado agora?", "Qual o faturamento de hoje?", "Qual carregador teve mais receita?", "Qual o horário de pico?", "Quantas sessões foram feitas hoje?".

> **Nota de ambiente — desenvolvimento no Colab:** como `chargegrid.db` e `ev_chargegrid.py` não persistem no Colab, o notebook precisa começar com duas células isoladas: uma de upload com validação dos dois arquivos, e outra importando as 4 funções do Raul só depois de confirmado o upload. Ver estrutura de referência no canal do time.

---

### 🔴 Luan

**Entrega 1 — `dashboard.py` com Streamlit | Prazo: 14/07**
Importa as 4 funções do Raul (mais `inicializar_banco()`, chamada uma vez no início para garantir que o banco existe). O dashboard mostra: status de cada carregador (Livre/Ocupada), potência ativa, kWh consumidos, receita do dia e total de sessões. Atualização automática a cada 30 segundos. Roda com `streamlit run dashboard.py`, sem servidor separado. Para testar, usa as placas já cadastradas: `ABC1D23`, `XYZ9F88`, `GHI3K45`, `DEF7M01`.

**Entrega 2 — Protótipos navegáveis Totem + App + QR Pix | Prazo: 14/07**
Pode rodar em paralelo com o dashboard. Fluxo do Totem: boas-vindas → digitar placa → validação → seleção de carregador disponível → acompanhamento da sessão → encerramento com QR Code de pagamento (a URL já vem pronta no campo `url` do retorno do pagamento; se o Raul ativar o Mercado Pago real, vira um QR PIX de verdade). App é o mesmo fluxo adaptado para tela pequena. Não precisa programar um app real — só o design navegável, em Figma ou HTML.

---

### ⚪ Pedro

**07/07** — Recebe `modelo_demanda.pkl` do Kevin e integra no `ev_chargegrid.py`, substituindo `DEMANDA_PREVISTA_POR_HORA` pela chamada ao modelo treinado.

**25/07** — Integração final de todos os módulos. Roda o checklist completo: demo grava no banco, dashboard mostra dados, chatbot responde com números reais, protótipos navegam sem erro, QR Code aparece no encerramento.

**Até meados de agosto** — Vídeo de demonstração completo, slides finais (problema, solução, arquitetura, demonstração, resultados comerciais) e submissão conforme os critérios do EV Challenge 2026.

---

## Status Consolidado do Kanban

| Card | Responsável | Prazo | Status |
|------|-------------|-------|--------|
| Sistema Base Python (`ev_chargegrid.py`) | Time | — | ✅ Concluído |
| DLB — Balanceamento Dinâmico de Carga | Time | — | ✅ Concluído |
| Simulação Protocolo OCPP 1.6J | Time | — | ✅ Concluído |
| Análise Comercial Base (planilha SP2) | Kevin | — | ✅ Concluído |
| Banco de dados + autenticação + pagamento (backend completo) | Raul | — | ✅ Concluído |
| 4 funções de leitura (API interna) | Raul | — | ✅ Concluído |
| Mercado Pago real (opcional) | Raul | antes de 25/07 | 🔵 Opcional |
| `dados_rag.json` | Kevin | 24/06 | 📋 Para fazer |
| `requirements.txt` | Kevin | 24/06 | 📋 Para fazer |
| `modelo_demanda.pkl` + notebook + gráfico | Kevin | 07/07 | ⏳ Backlog |
| Roteador de tempo real no `buscar_contexto()` | Lucas | 30/06 | 🔄 Em andamento |
| Substituição dos 12 documentos por `dados_rag.json` | Lucas | 11/07 | ⏳ Backlog |
| Notebook Sprint 3 + `resultados_testes_sprint3.json` | Lucas | 21/07 | ⏳ Backlog |
| `dashboard.py` com Streamlit | Luan | 14/07 | 📋 Para fazer |
| Protótipos Totem + App + QR Pix | Luan | 14/07 | 📋 Para fazer |
| Integração do modelo ML no motor | Pedro | 07/07 | ⏳ Backlog |
| Integração final + checklist | Pedro | 25/07 | ⏳ Backlog |
| Vídeo + slides + submissão | Pedro | meados de agosto | ⏳ Backlog |

---

## Dependências Críticas entre Módulos

```
Raul já entregou banco + autenticação + pagamento + 4 funções de leitura
    ├── Lucas usa as funções no roteador de tempo real (prazo 30/06)
    └── Luan usa as funções no dashboard (prazo 14/07)

Kevin entrega dados_rag.json (prazo 24/06)
    └── Lucas substitui os 12 documentos fixos (prazo 11/07)

Kevin entrega modelo_demanda.pkl (prazo 07/07)
    └── Pedro integra no motor (mesmo prazo, 07/07)

Lucas conclui as duas frentes do chatbot (prazo 21/07)
Luan conclui dashboard + protótipos (prazo 14/07)
    └── Pedro faz a integração final (prazo 25/07)
        └── Vídeo + slides + submissão (até meados de agosto)
```

**Regra prática:** se alguém está bloqueado esperando outra parte, avisa o Pedro imediatamente. Bloqueio silencioso é o maior risco do projeto.

---

## Regra de Entrega para o Pedro

Cada integrante entrega ao Pedro com os seguintes três itens obrigatórios:

| Item | O que é |
|------|---------|
| Arquivo produzido | `.py`, `.ipynb`, `.pkl`, `.json`, `.html`, `.fig` ou similar |
| Evidência de funcionamento | Print, vídeo curto (30s), log ou screenshot mostrando que funciona |
| Instruções de integração | O que Pedro precisa saber para encaixar a entrega sem quebrar o que já existe |

> **Tarefa colaborativa ou com handoff (ex: Kevin → Lucas):** quem depende do outro só assume a entrega depois de receber o arquivo combinado. Pedro não integra metades separadas — cada etapa chega funcionando antes de passar para a próxima.

**Checklist da integração final (25/07):** demo grava no banco → dashboard mostra dados reais → chatbot responde com números reais → protótipos navegam sem erro → QR Code aparece no encerramento da sessão.

---

*Atualizar este documento sempre que um card mudar de coluna no Trello ou um prazo for ajustado.*
