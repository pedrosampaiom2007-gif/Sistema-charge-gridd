# ChargeGrid Intelligence

Sistema de gestão comercial de recarga de veículos elétricos, desenvolvido para o EV Challenge 2026 (GoodWe / FIAP). Cobre o ciclo completo de uma sessão de recarga comercial: autoatendimento no totem, cobrança via Pix simulado, painel operacional para o gestor, previsão de demanda por IA e um assistente conversacional que responde com dados reais do sistema.

## Visão geral

O motor (`ev_chargegrid.py`) controla até 10 estações de recarga: autenticação de motorista por placa (hash SHA-256, com mascaramento em conformidade com a LGPD), balanceamento de carga entre estações ativas (DLB), tarifação dinâmica por horário e demanda, e pagamento via gateway simulado (Mercado Pago sandbox). Uma API Flask expõe esse motor para dois clientes web — o totem do motorista e o dashboard do gestor — e um notebook de chatbot consulta o mesmo banco de dados para responder perguntas em linguagem natural, combinando dados em tempo real com um histórico de 60 sessões reais.

## Arquitetura

```
Totem (entregas/files/)                Dashboard (entregas/frontend/)
        │  HTTP/JSON                            │  HTTP/JSON
        └──────────────┐         ┌──────────────┘
                        ▼         ▼
              API Flask (entregas/files/api_server.py)
                        │
                        ▼
         Motor (entregas/ev_chargegrid.py)
                        │
                        ▼
      SQLite — entregas/chargegrid.db (CHARGEGRID_DB)
                        ▲
                        │  leitura direta (mesmas funções do motor)
                        │
        Chatbot (entregas/ChargeGrid_Intelligence_chatbot.ipynb)
                        │
                        ▼
        Ollama local (llama3.2:3b) + dados_rag.json (histórico)
```

A previsão de demanda por IA (`modelo_demanda.pkl`, um RandomForest treinado com dados reais) não é um sistema à parte — ela é chamada de dentro do próprio motor (`ia_prever_demanda`), tanto na tarifação de cada sessão quanto na leitura que alimenta o gráfico de demanda do dashboard.

O motor é a única fonte de verdade: API, dashboard, totem e chatbot leem dele (direta ou indiretamente) — nenhum desses componentes duplica lógica de negócio.

## Estrutura do repositório

```
entregas/
├── ev_chargegrid.py                    motor: banco, auth, pagamento, DLB, IA preditiva
├── dados_rag.json                      histórico de 60 sessões reais (base do RAG do chatbot)
├── modelo_demanda.pkl                  modelo RandomForest treinado (previsão de demanda)
├── requirements (1).txt                dependências Python
├── ChargeGrid_Intelligence_chatbot.ipynb   chatbot (roda no Google Colab)
├── files/                              totem do motorista (self-service) + api_server.py
│   ├── api_server.py                   camada Flask que expõe o motor via HTTP/JSON
│   ├── index.html / app.js / style.css
└── frontend/                           dashboard do gestor
    └── index.html / app.js / style.css

modelagem_ia/
└── IA aplicada.zip                     notebook de treino do modelo + gráfico comparativo
```

## Como executar

**1. API (backend):**
```bash
cd entregas/files
pip install -r "../requirements (1).txt" flask flask-cors
python api_server.py
```
Sobe em `http://localhost:5000`. Na primeira execução, popula o banco com 4 placas de teste (`ABC1D23`, `XYZ9F88`, `GHI3K45`, `DEF7M01`).

**2. Dashboard (gestor):** abra `entregas/frontend/index.html` no navegador, ou sirva com `python -m http.server 5500` dentro da pasta.

**3. Totem (motorista):** abra `entregas/files/index.html` no navegador. Cada totem físico serve uma única estação: use `?estacao=3` na URL para escolher qual (padrão é a estação 1).

Se a API rodar em outro host/porta, ajuste a constante `API_BASE` no topo de `app.js` (dashboard e totem).

**4. Chatbot:** abra `ChargeGrid_Intelligence_chatbot.ipynb` no Google Colab (ele só roda lá — instala Ollama e depende de comandos específicos do Colab). Quando pedido, faça upload de `ev_chargegrid.py`, `dados_rag.json`, `modelo_demanda.pkl` e do `chargegrid.db` **atual** (o mesmo arquivo que a API gerou) — sem esse último, o chatbot responde só com o histórico, não com dados em tempo real.

## Fluxo principal (totem → API → banco → dashboard → chatbot)

1. Motorista inicia a sessão no totem → `POST /api/sessoes/iniciar` na API.
2. A API valida a placa contra o banco e grava a sessão em `chargegrid.db`.
3. O dashboard, que faz polling em `GET /api/painel` a cada poucos segundos, reflete a estação ocupada, o consumo e o valor acumulado.
4. Ao encerrar (`POST /api/sessoes/<n>/encerrar`), a API gera a cobrança simulada, o totem mostra o QR Pix e emite o recibo.
5. O chatbot, com o `chargegrid.db` atualizado, consulta as mesmas funções de leitura do motor e responde perguntas sobre o estado real do sistema — sem depender da API estar no ar no momento da pergunta.

## O que já foi resolvido

- Motor completo: banco SQLite, autenticação com hash, mascaramento LGPD, pagamento sandbox, balanceamento de carga.
- Modelo de IA preditiva treinado com dados reais e integrado ao motor.
- API Flask cobrindo todas as ações do motor (sessões, painel, KPIs, curva de demanda).
- Dashboard e totem funcionais, testados ponta a ponta com dados reais passando pelo sistema.
- Chatbot com roteador de tempo real (banco) vs. histórico (RAG), rodando com LLM local sem custo.
- Correções de integração já validadas: função de leitura de potência por estação, remoção de uma cópia duplicada da API, caminho de importação do motor corrigido, e o banco SQLite unificado num único arquivo para todos os processos locais.

## Limitações conhecidas

- **Não rode o script de console (`python ev_chargegrid.py`) ao mesmo tempo que a API.** SQLite permite um escritor por vez; dois processos gravando ao mesmo instante podem gerar erro de "banco travado". Não é um bug do projeto — é uma característica do SQLite com múltiplos processos.
- A opção 5 do menu de console (demonstração comercial) grava sessões de teste no mesmo banco usado pela API/dashboard/chatbot e não fecha todas (estações 2, 3 e 4 ficam marcadas como ocupadas). Se for usada, apague `entregas/chargegrid.db` antes de uma demonstração real.
- `potencia_kw` de cada estação existe só na memória do processo da API — se ela reiniciar, as estações voltam a mostrar 0 kW até uma nova sessão começar (o histórico de kWh e valor no banco não é afetado).
- O chatbot não enxerga o banco automaticamente: é preciso reenviar o `chargegrid.db` atual ao Colab sempre que quiser respostas com dados em tempo real atualizados.
- `requirements (1).txt` não inclui `flask`/`flask-cors` — instale-os junto, como no comando acima.

## Equipe

Pedro Sampaio, Raul Sampaio, Lucas Garcia, Luan de Araujo, Kevin Rodrigues — EV Challenge 2026, GoodWe / FIAP.
