# ChargeGrid Intelligence — Responsabilidades do Projeto

> Referência central de ownership para todos os integrantes.  
> Atualizado pelo líder do projeto (Pedro) a cada sprint.  
> EV Challenge 2026 — GoodWe / FIAP

---

## Equipe e Etiquetas do Trello

| Etiqueta | Integrante | RM | Função |
|----------|------------|----|--------|
| ⚪ Sem etiqueta | Pedro Sampaio Mochnacs Arruda | RM 573522 | Líder, coordenador e integrador final |
| 🔵 Azul | Raul Sampaio Mochnacs Arruda | RM 573523 | Backend — banco de dados, autenticação e pagamentos |
| 🟡 Amarela | Lucas Garcia de Britto | RM 571768 | IA e Chatbot — RAG, LLM e integração de dados |
| 🔴 Vermelha | Luan de Araujo Carneiro | RM 573691 | Frontend e UI — dashboard, protótipos e telas |
| 🟢 Verde | Kevin Rodrigues de Melo | RM 571777 | Dados e ML — análise comercial e IA preditiva |

> **Cards com duas etiquetas = tarefa colaborativa.** Cada membro executa uma frente específica dentro da mesma tarefa. A integração entre as duas partes é responsabilidade dos próprios membros — Pedro só recebe quando estiver funcionando de ponta a ponta.

---

## Arquitetura da Solução Final

```
ev_chargegrid.py  ← Motor principal do sistema (base de tudo)
│
├── [🔵 Raul]   Banco de Dados SQLite — grava sessões em tempo real
├── [🔵 Raul]   Autenticação e Criptografia
├── [🔵 Raul]   Gateway de Pagamentos (Mercado Pago Sandbox)
├── [🟢 Kevin]  IA Preditiva — modelo ML treinado com dados reais (.pkl)
└──             OCPP 1.6J + DLB ✅ Concluído

chargegrid.db  ← Banco de dados SQLite gerado pelo sistema em tempo real
│
├── [🟡 Lucas]  Chatbot lê o banco para responder com dados reais
├── [🔴 Luan]   Dashboard consome o banco para exibir status ao vivo
└── [🟢 Kevin]  Modelo ML treinado com histórico do banco + planilha SP2

ChargeGrid_Intelligence_Sprint3.ipynb  ← Chatbot evoluído
├── [🟢🟡 Kevin + Lucas]  RAG com dados reais da planilha SP2
└── [🟡 Lucas]            Integração com banco de dados em tempo real

Interface Visual
├── [🔴 Luan]  Dashboard de Monitoramento em Tempo Real
└── [🔴 Luan]  Protótipos de Tela — Totem + App + QR Pix

Entrega Final
└── [Pedro]    Integração, revisão, vídeo e apresentação
```

---

## Entendendo os Componentes Principais

### O que é o banco de dados e por que não é o Excel

A planilha `Trabalho_Analise_Comercial_SP2.xlsx` é um arquivo de análise histórica — dados preenchidos manualmente para estudar o comportamento do sistema. Ela é estática: alguém abre, lê, fecha. Não muda sozinha enquanto o sistema roda.

O banco de dados é diferente: é onde o `ev_chargegrid.py` grava automaticamente cada evento em tempo real — toda sessão que começa, todo kWh consumido, todo pagamento processado. É o "diário de bordo" automático do sistema.

Para este projeto usamos **SQLite** — um banco de dados que fica em um único arquivo `.db` na pasta do projeto, sem precisar instalar nenhum servidor. O Python já tem suporte nativo via `import sqlite3`.

```python
# Como o banco é criado (Raul faz isso uma vez no ev_chargegrid.py)
import sqlite3

conn = sqlite3.connect("chargegrid.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessoes (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        id_estacao     INTEGER,
        id_usuario     TEXT,
        hora_inicio    INTEGER,
        kwh_consumidos REAL,
        valor_sessao   REAL,
        pagamento      TEXT,
        encerrada      INTEGER DEFAULT 0
    )
""")
conn.commit()
```

A partir daí, o arquivo `chargegrid.db` passa a ser a fonte de verdade do sistema. Lucas, Kevin e Luan todos consomem dados desse arquivo — cada um do seu jeito.

**Resumo das responsabilidades de cada fonte de dados:**

| Fonte | O que contém | Quem usa | Para quê |
|-------|-------------|----------|----------|
| `Trabalho_Analise_Comercial_SP2.xlsx` | Dados históricos de análise | Kevin, Lucas | Treinar o modelo ML e enriquecer o RAG |
| `chargegrid.db` | Sessões em tempo real geradas pelo sistema | Raul, Lucas, Kevin, Luan | Tudo que precisa refletir o estado atual do sistema |

---
Por que duas fontes? O SQLite responde o agora — vaga livre, consumo ativo, status do carregador. O Excel responde o histórico — receita por mês, pico de demanda, ROI. Separar as camadas operacional e estratégica é o que transforma o chatbot em ferramenta de decisão real, não só um painel de texto.


### O que são os 12 documentos estáticos do Sprint 2

No notebook do Sprint 2, o chatbot funciona assim:

```python
documentos = [
    "CP-03 gerou 312 kWh e R$ 280,80 de receita em maio.",
    "CP-02 gerou 241 kWh e R$ 216,90 de receita em maio.",
    "CP-01 gerou 198 kWh e R$ 178,20 de receita em maio.",
    "CP-05 gerou 209 kWh e R$ 188,10 de receita em maio.",
    "CP-04 gerou 175 kWh e R$ 157,50 de receita em maio.",
    "CP-01 está ocupado. CP-02 está livre. CP-03 está ocupado...",
    "Tarifa padrão: R$ 0,90/kWh. Tempo médio de sessão: 38 minutos.",
    "Hoje foram realizadas 47 sessões de recarga, das 06h00 às 22h30.",
    "Pico de demanda previsto entre 17h e 20h...",
    "Para 50 veículos/dia recomenda-se ao menos 3 carregadores de 22 kW.",
    "Cobrança feita por kWh consumido ou por tempo de sessão...",
    "Custo médio de instalação por ponto de carga: R$ 15.000...",
]
```

São 12 frases digitadas na mão que simulam o que o sistema "sabe". O problema: são dados inventados e nunca mudam. O chatbot vai responder para sempre que "hoje foram 47 sessões" e que "CP-01 está ocupado" — mesmo que o sistema esteja rodando com uma realidade completamente diferente.

**O objetivo do Sprint 3 é substituir essas 12 frases por dados reais** — vindos da planilha SP2 e do banco `chargegrid.db`. Com isso o chatbot passa a responder com informações verdadeiras e atualizadas.

---

### Como funciona o modelo de IA preditiva (tarefa do Kevin)

No `ev_chargegrid.py` hoje existe este dicionário:

```python
DEMANDA_PREVISTA_POR_HORA = {
     0: 0.05,  1: 0.03,  2: 0.03,  3: 0.03,
     6: 0.20,  7: 0.45,  8: 0.70,  9: 0.80,
    12: 1.00, 13: 0.85, 18: 1.00, 19: 1.00,
    ...
}
```

Esses números foram digitados na intuição por quem escreveu o código — "às 12h deve estar cheio, às 3h da manhã deve estar vazio". É um chute educado, mas continua sendo um chute.

**scikit-learn** é uma biblioteca Python que aprende padrões a partir de dados reais em vez de intuição. O Kevin vai:

1. Pegar os dados reais da planilha SP2 (sessões por horário do dia)
2. Treinar um modelo que aprende: *"dado que são X horas, qual é o fator de demanda real?"*
3. Salvar esse modelo como `modelo_demanda.pkl` com a biblioteca `joblib`
4. O Pedro substitui o dicionário fixo pelo modelo treinado no `ev_chargegrid.py`:

```python
import joblib

modelo_ml = joblib.load("modelo_demanda.pkl")

def ia_prever_demanda(hora: int) -> float:
    return float(modelo_ml.predict([[hora]])[0])
```

O resultado prático: a previsão de demanda passa a ser baseada nos dados reais do projeto, não em números que alguém chutou. A diferença entre *"eu acho que vai ter pico às 18h"* e *"os dados mostram que o pico real é às 19h30"*.

---

## Tarefas Colaborativas

### 🔵🔴 Autenticação e Criptografia — Raul + Luan
**Status:** Em andamento, Já pode iniciar

Autenticação precisa de backend e frontend ao mesmo tempo. O Raul faz a lógica que valida o usuário; o Luan faz as telas por onde o usuário passa. Um sem o outro não funciona.

**Raul faz (backend):**
- Implementar verificação de identidade antes de liberar `iniciar_sessao()` — o sistema só abre a sessão se o usuário for válido
- Criptografar os dados sensíveis do usuário (hash da placa ou token de sessão gerado no momento do login)
- Retornar um token ou booleano que o frontend consome para liberar ou bloquear a tela

**Luan faz (frontend):**
- Tela de autenticação no Totem e no App: campo para digitar placa ou ID → sistema valida → carregador liberado ou acesso negado
- Feedback visual claro: aprovado (verde) / negado (vermelho) / aguardando validação (loading)
- As telas de autenticação aqui devem ser consistentes com a lógica que o Raul implementou

**Ponto de encontro obrigatório:** antes de cada um começar a sua parte, Raul e Luan precisam combinar o contrato entre backend e frontend — o que o backend retorna (token? True/False? objeto JSON?) e como o frontend consome isso. Cinco minutos de alinhamento evitam retrabalho de horas.

**Entregam juntos para Pedro:** fluxo de autenticação funcionando de ponta a ponta — usuário digita placa na tela do Luan, backend do Raul valida, carregador é liberado ou negado.

---

### 🔵🟡 Integração com Base de Dados — Raul + Lucas
**Status:** Em andamento, Já pode iniciar

O banco `chargegrid.db` serve a dois módulos: o motor Python do Raul e o chatbot do Lucas. A divisão garante que um não bloqueie o outro.

**Raul faz (backend):**
- Criar o arquivo `chargegrid.db` com o schema de sessões (conforme exemplo na seção anterior)
- Substituir a lista `estacoes[]` do `ev_chargegrid.py` por gravações reais no banco: INSERT ao iniciar sessão, UPDATE ao encerrar com consumo e valor final
- Disponibilizar uma função de leitura que o Lucas e o Luan possam chamar sem mexer no motor principal

**Lucas faz (IA/chatbot):**
- Adaptar a função `buscar_contexto()` do chatbot para consultar o banco em vez dos 12 documentos fixos
- Exemplo do que o chatbot precisa conseguir responder com dados reais: *"Quais carregadores estão ativos agora?"*, *"Qual o faturamento de hoje?"*
- Não precisa esperar o banco estar 100% pronto — pode desenvolver com mock do banco e integrar depois

**Ponto de encontro obrigatório:** Raul define e compartilha o schema da tabela (nomes das colunas, tipos) antes de Lucas começar a escrever as queries do chatbot. Se o schema mudar depois, as queries do Lucas quebram.

**Entregam juntos para Pedro:** banco populado com dados de sessões reais + chatbot lendo e respondendo com esses dados.

---

### 🟢🟡 Chatbot RAG com Base de Dados Excel — Kevin + Lucas
**Status:** Em andamento, Já pode iniciar

Kevin domina os dados e sabe o que a planilha contém. Lucas domina o pipeline do chatbot. Juntos substituem os 12 documentos estáticos por dados reais da planilha SP2.

**Kevin faz (dados):**
- Processar a planilha `Trabalho_Analise_Comercial_SP2.xlsx` e transformar as informações relevantes em texto estruturado que o chatbot consiga indexar
- Identificar quais métricas da planilha são mais úteis para o chatbot responder: receita por carregador, sessões por dia, pico de horário, ticket médio
- Entregar os dados em formato combinado com o Lucas (CSV limpo, JSON ou blocos de texto)

**Lucas faz (chatbot):**
- Substituir os 12 documentos estáticos pela base preparada pelo Kevin
- Atualizar `buscar_contexto()` para buscar nos dados reais, não em strings fixas
- Rodar todos os casos de teste e gerar o `resultados_testes_sprint3.json`

**Ponto de encontro obrigatório:** Kevin e Lucas combinam o formato dos dados antes de Kevin começar a processar. Se Kevin entrega CSV e Lucas espera JSON, é retrabalho.

**Entregam juntos para Pedro:** chatbot respondendo perguntas com dados reais da planilha SP2, não com dados inventados do Sprint 2.

---

## Tarefas Individuais

### 🔵 Raul — Módulo de Faturamento + Gateway de Pagamentos
**Status:** Para fazer | Iniciar após: Autenticação e Banco de Dados

O sistema hoje imprime o recibo no terminal. O objetivo é disparar uma cobrança real via API.

**O que fazer:**
- Na função `encerrar_sessao()` do `ev_chargegrid.py`, substituir o `print()` do recibo por uma chamada à API do **Mercado Pago Sandbox** (ambiente de testes, sem dinheiro real)
- Enviar: valor da sessão, método de pagamento (PIX/Cartão/QRCode) e ID do usuário
- Receber confirmação de pagamento antes de liberar a vaga do posto
- Gravar o resultado da cobrança no banco `chargegrid.db`

**Entrega para Pedro:** `ev_chargegrid.py` com gateway integrado + screenshot ou log de uma cobrança de teste bem-sucedida no Sandbox.

---

### 🔴 Luan — Dashboard de Monitoramento em Tempo Real
**Status:** Para fazer | Pode iniciar: Agora, em paralelo

O dashboard é a interface do operador do posto — status de todas as estações, potência ativa e receita sem abrir o terminal.

**O que fazer:**
- Criar dashboard em HTML/React consumindo os dados do banco `chargegrid.db` ou, enquanto o banco não estiver pronto, usando dados simulados do `ev_chargegrid.py`
- Exibir o que a função `painel_operacional()` já calcula: status de cada estação (livre/ocupada/manutenção), potência ativa por estação, kWh consumidos, receita acumulada do dia
- Atualização periódica dos dados (polling a cada 30s é suficiente)

**Entrega para Pedro:** Dashboard funcionando com dados visíveis + link ou arquivo navegável.

---

### 🔴 Luan — Protótipos de Tela — Totem + App + QR Pix
**Status:** Para fazer | Pode iniciar: Agora, independente do backend

**O que fazer:**
- **Totem:** tela de boas-vindas → autenticação por placa → seleção de carregador disponível → acompanhamento da sessão em tempo real → encerramento com QR para pagamento
- **App:** versão mobile do mesmo fluxo
- **QR Pix:** tela gerada ao encerrar a sessão com o valor a pagar e o QR Code do PIX

As telas de autenticação aqui devem ser consistentes com o fluxo que o Raul implementou no backend.

**Entrega para Pedro:** Protótipos navegáveis (Figma, HTML ou similar) cobrindo os três fluxos.

---

### 🟢 Kevin — IA Preditiva Real — Substituição do Dicionário por ML
**Status:** Backlog | Iniciar após: Parte do RAG com Lucas estar encaminhada

**O que fazer:**
1. Usar os dados de horário e volume de sessões da planilha SP2 para treinar um modelo de regressão com `scikit-learn`
2. O modelo aprende: *"dado que são X horas do dia, qual é o fator de demanda esperado?"*
3. Exportar o modelo como `modelo_demanda.pkl` usando `joblib`
4. O Pedro integra no `ev_chargegrid.py` substituindo o dicionário fixo:

```python
import joblib
modelo_ml = joblib.load("modelo_demanda.pkl")

def ia_prever_demanda(hora: int) -> float:
    return float(modelo_ml.predict([[hora]])[0])
```

**Entrega para Pedro:** Notebook de treinamento do modelo + arquivo `modelo_demanda.pkl` + gráfico comparando a previsão do modelo com o dicionário original.

---

### 🟡 Lucas — Chatbot: Integração com Dados em Tempo Real
**Status:** Backlog | Iniciar após: Banco de dados do Raul estar funcional

Esta é a etapa final do chatbot — depois que o RAG com Excel e o banco de dados estiverem prontos, o chatbot passa a responder sobre o estado atual do sistema.

**O que fazer:**
- Conectar a função `buscar_contexto()` ao banco `chargegrid.db` do Raul para responder sobre o estado atual
- Perguntas que devem funcionar: *"Qual carregador está ocupado agora?"*, *"Qual o faturamento de hoje?"*, *"Tem algum carregador em manutenção?"*
- Atualizar o `SYSTEM_PROMPT` se necessário para refletir que o chatbot agora tem acesso a dados em tempo real

**Entrega para Pedro:** Chatbot respondendo perguntas com dados do banco em tempo real + JSON de testes atualizado (`resultados_testes_sprint3.json`).

---

### Pedro — Apresentação Final do Projeto
**Status:** Backlog | Inicia quando: Módulos principais integrados

**O que fazer:**
- Integrar todos os módulos recebidos dos membros no repositório final
- Gravar o vídeo de demonstração completo (substituindo o vídeo parcial atual) mostrando o sistema de ponta a ponta: sessão iniciada → autenticação → carregamento → chatbot respondendo → pagamento → dashboard atualizado
- Consolidar slides: problema, solução, arquitetura, demonstração, resultados comerciais
- Submeter o projeto conforme os critérios do EV Challenge 2026

---

## Status Consolidado do Kanban

| Card | Tipo | Responsáveis | Status |
|------|------|-------------|--------|
| Sistema Base Python (`ev_chargegrid.py`) | Conjunto | Time | ✅ Concluído |
| DLB — Balanceamento Dinâmico de Carga | Conjunto | Time | ✅ Concluído |
| Simulação Protocolo OCPP 1.6J | Conjunto | Time | ✅ Concluído |
| Análise Comercial Base (planilha SP2) | Individual | Kevin | ✅ Concluído |
| Documentação técnica | Individual | Pedro | ✅ Concluído |
| Vídeo de demonstração parcial | Individual | Pedro | ✅ Concluído |
| 🔵🔴 Autenticação e Criptografia | Colaborativa | Raul + Luan | 🔄 Em andamento |
| 🔵🟡 Integração com Base de Dados | Colaborativa | Raul + Lucas | 🔄 Em andamento |
| 🟢🟡 Chatbot RAG com Excel | Colaborativa | Kevin + Lucas | 🔄 Em andamento |
| 🔵 Faturamento + Gateway de Pagamentos | Individual | Raul | 📋 Para fazer |
| 🔴 Dashboard de Monitoramento em Tempo Real | Individual | Luan | 📋 Para fazer |
| 🔴 Protótipos de Tela — Totem + App + QR Pix | Individual | Luan | 📋 Para fazer |
| 🟢 IA Preditiva Real (ML) | Individual | Kevin | ⏳ Backlog |
| 🟡 Chatbot com Dados em Tempo Real | Individual | Lucas | ⏳ Backlog |
| Apresentação Final do Projeto | Individual | Pedro | ⏳ Backlog |

---

## Dependências Críticas entre Módulos

```
Raul cria o banco (chargegrid.db)
    ├── Lucas pode conectar o chatbot ao banco
    ├── Luan pode consumir os dados no dashboard
    └── Kevin pode usar o histórico para melhorar o modelo ML

Kevin processa a planilha SP2
    └── Lucas pode substituir os 12 documentos estáticos no RAG

Raul + Luan concluem a autenticação
    └── Luan finaliza os protótipos de tela com o fluxo completo

Lucas conclui o RAG com Excel (com Kevin)
    └── Lucas avança para a integração com dados em tempo real
```

**Regra prática:** se você está bloqueado esperando outra parte, avise o Pedro imediatamente. Bloqueio silencioso é o maior risco do projeto.

---

## Regra de Entrega para o Pedro

Cada integrante entrega ao Pedro com os seguintes três itens obrigatórios:

| Item | O que é |
|------|---------|
|  Arquivo produzido | `.py`, `.ipynb`, `.pkl`, `.html`, `.fig` ou similar |
|  Evidência de funcionamento | Print, vídeo curto (30s), log ou screenshot mostrando que funciona |
|  Instruções de integração | O que Pedro precisa saber para encaixar a entrega sem quebrar o que já existe |

> **Tarefa colaborativa:** os dois membros entregam juntos, já integrados entre si. Pedro não integra metades separadas de uma tarefa colaborativa — ela chega funcionando de ponta a ponta.

---

*Atualizar este documento sempre que um card mudar de coluna no Trello.*
