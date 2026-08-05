# ChargeGrid Intelligence

Sistema de gestão comercial de recarga de veículos elétricos, desenvolvido para o EV Challenge 2026 (GoodWe / FIAP). Cobre o ciclo completo de uma sessão de recarga comercial: autoatendimento no totem, cobrança via Pix simulado, painel operacional para o gestor (com login), uma área pessoal do motorista (histórico de pagamentos, suporte a mais de um carro por conta) e um assistente conversacional que responde tanto sobre o sistema quanto dúvidas gerais de carro elétrico.

## Visão geral

O motor (`entregas/ev_chargegrid.py`) controla até 10 estações de recarga: autenticação de motorista por placa (hash SHA-256, com mascaramento em conformidade com a LGPD), balanceamento de carga entre estações ativas (DLB), tarifação dinâmica por horário e demanda, e pagamento via gateway simulado (Mercado Pago sandbox). Uma API Flask expõe esse motor para três clientes web (totem, dashboard, app do motorista) e um chatbot (rodando local ou no Colab) que responde em linguagem natural, combinando dados em tempo real com um histórico de 60 sessões reais.

**O banco de dados é Postgres na nuvem (Supabase), não um arquivo local** — qualquer processo, de qualquer computador com a credencial certa, lê e escreve no mesmo banco. **A IA do chatbot roda na nuvem (Groq)**, não localmente — não depende de instalar nem baixar modelo nenhum.

## Arquitetura

```
entregas/index.html (landing — escolha: motorista / minha conta / administrador)
        │
        ├── Totem (entregas/files/)           self-service na estação, sem login
        ├── App do motorista (entregas/app/)  login por placa, histórico, chat
        └── Dashboard (entregas/frontend/)    login admin, dado agregado
                        │  HTTP/JSON (todos os três)
                        ▼
              API Flask (entregas/files/api_server.py)
                        │
                        ▼
         Motor (entregas/ev_chargegrid.py)
                        │
                        ▼
        Postgres — Supabase (DATABASE_URL no .env, não versionado)
                        ▲
                        │  mesmas funções de leitura do motor
                        │
        Chatbot — entregas/chatbot.py (local) OU
                  ChargeGrid_Intelligence_chatbot.ipynb (Colab)
                        │
                        ▼
        Groq (llama-3.1-8b-instant, nuvem) + dados_rag.json (histórico)
```

A previsão de demanda por IA (`modelo_demanda.pkl`, um RandomForest treinado com dados reais) é chamada de dentro do próprio motor (`ia_prever_demanda`), tanto na tarifação de cada sessão quanto na leitura que alimenta o gráfico de demanda do dashboard.

O motor é a única fonte de verdade: API, dashboard, totem, app do motorista e chatbot leem dele (direta ou indiretamente) — nenhum desses componentes duplica lógica de negócio.

## Estrutura do repositório

```
.env                                  DATABASE_URL + GROQ_API_KEY — NÃO existe no repo, veja "Configuração"
entregas/
├── ev_chargegrid.py                  motor: banco, auth, contas, pagamento, DLB, IA preditiva
├── chatbot.py                        chatbot em terminal, local, sem Colab (mesma lógica do notebook)
├── dados_rag.json                    histórico de 60 sessões reais (base do RAG do chatbot)
├── modelo_demanda.pkl                modelo RandomForest treinado (previsão de demanda)
├── requirements (1).txt              dependências Python (o nome do arquivo é esse mesmo, com espaço)
├── ChargeGrid_Intelligence_chatbot.ipynb   chatbot em notebook (roda no Google Colab)
├── index.html                        landing page — escolhe motorista / minha conta / admin
├── files/                            totem do motorista (self-service) + api_server.py
│   ├── api_server.py                 camada Flask que expõe o motor via HTTP/JSON
│   └── index.html / app.js / style.css
├── app/                              área pessoal do motorista — login por placa
│   └── index.html / app.js / style.css
└── frontend/                         dashboard do gestor — login admin
    └── index.html / app.js / style.css

modelagem_ia/
└── IA aplicada.zip                   notebook de treino do modelo + gráfico comparativo
```

## Configuração (só na primeira vez)

Crie um arquivo `.env` na raiz do repositório (mesmo nível deste README) com:
```
DATABASE_URL=postgresql://usuario:senha@host:porta/postgres
GROQ_API_KEY=gsk_...
```
Esse arquivo **nunca é commitado** (está no `.gitignore`, de propósito — tem senha de banco e chave de API). `DATABASE_URL` é a connection string do Supabase (use o modo **Session pooler**, não o "Direct connection" — o direct costuma resolver só em IPv6 e falha em várias redes). `GROQ_API_KEY` vem em console.groq.com → API Keys.

## Como executar

**1. API (backend):**
```bash
cd entregas/files
pip install -r "../requirements (1).txt"
python api_server.py
```
Sobe em `http://localhost:5000`. Na primeira execução, popula o banco com 4 placas de teste (`ABC1D23`, `XYZ9F88`, `GHI3K45`, `DEF7M01`) e um admin de teste (`admin` / `chargegrid2026` — troque antes de uma apresentação real).

**2. Landing page:** abra `entregas/index.html` no navegador — escolha motorista, minha conta ou administrador.

**3. Totem (motorista, na estação):** `entregas/files/index.html`. Cada totem físico serve uma única estação: use `?estacao=3` na URL (padrão é a estação 1).

**4. App do motorista:** `entregas/app/index.html` — login só com a placa. Mostra histórico de pagamentos (de todos os carros vinculados à mesma conta) e o chat.

**5. Dashboard (gestor):** `entregas/frontend/index.html` — pede login antes de mostrar qualquer coisa.

**6. Chatbot local (sem Colab):**
```bash
cd entregas
python chatbot.py
```
**Chatbot no Colab (alternativa):** abra `ChargeGrid_Intelligence_chatbot.ipynb` no Google Colab. Ele baixa os arquivos necessários direto do GitHub — não precisa mais de upload manual. Só precisa configurar dois "Secrets" no Colab (ícone de chave 🔑): `DATABASE_URL` e `GROQ_API_KEY`, com os mesmos valores do seu `.env`.

Se a API rodar em outro host/porta, ajuste a constante `API_BASE` no topo de cada `app.js` (totem, dashboard, app).

## Fluxo principal (totem → API → banco → dashboard/app → chatbot)

1. Motorista inicia a sessão no totem → `POST /api/sessoes/iniciar` na API.
2. A API valida a placa contra o banco e grava a sessão no Postgres.
3. O dashboard (logado) e o próprio totem, que fazem polling em `GET /api/painel`, refletem a estação ocupada, o consumo e o valor acumulado.
4. Ao encerrar (`POST /api/sessoes/<n>/encerrar`), a API gera a cobrança simulada, o totem mostra o QR Pix e emite o recibo.
5. A qualquer momento, em qualquer lugar (não precisa ser no totem), o motorista abre o app, loga com a placa, e vê o histórico daquela sessão — e de qualquer outro carro vinculado à mesma conta.
6. O chatbot (local ou Colab) consulta as mesmas funções de leitura do motor, direto no Postgres — sem depender de nenhum arquivo local, sem precisar da API estar no ar.

## O que já foi resolvido

- Motor completo: banco Postgres (Supabase), autenticação com hash, mascaramento LGPD, pagamento sandbox, balanceamento de carga.
- **Contas com mais de um carro**: uma conta pode ter várias placas vinculadas; login com qualquer uma delas mostra o histórico combinado.
- Modelo de IA preditiva treinado com dados reais e integrado ao motor.
- API Flask cobrindo sessões, painel, KPIs, curva de demanda, login admin, histórico de pagamentos, vínculo de carro e chat.
- **Login de administrador** de verdade (usuário/senha, token), protegendo dado agregado (`/api/kpis`, `/api/demanda-ia`) — o `/api/painel` continua aberto porque o totem também precisa dele.
- Totem, dashboard e app do motorista funcionais, testados ponta a ponta com dados reais passando pelo sistema.
- Chatbot com roteador de tempo real (banco) vs. histórico (RAG) vs. dúvidas gerais de carro elétrico, rodando com Groq (nuvem, sem custo no uso normal) — disponível como script local ou notebook Colab, sem exigir upload manual de arquivo em nenhum dos dois.
- Recuperação automática de sessões ativas quando a API reinicia (evita duplicar sessão na mesma estação).
- Landing page única, separando claramente os três públicos (motorista no totem, motorista no app, administrador).

## Limitações conhecidas

- **O totem não tem login nem menu de navegação além do essencial** — de propósito. É um ponto de serviço físico, precisa ser rápido; funcionalidades "extras" (histórico, chat) ficam só no app do motorista, não no totem.
- `potencia_kw` de cada estação existe só na memória do processo da API — se ela reiniciar, as estações voltam a mostrar 0 kW até o próximo ciclo de simulação (o histórico de kWh e valor no banco não é afetado; a sessão em si é recuperada corretamente).
- A opção 5 do menu de console (`python ev_chargegrid.py`, demonstração comercial) ainda não fecha todas as sessões que abre — se for usada antes de uma apresentação real, confira o painel depois.
- A integração com hardware de carregador real (protocolo OCPP) é só simulada (a função correspondente imprime uma mensagem, não fala com equipamento nenhum) — a lógica de negócio e a interface são reutilizáveis, a comunicação com hardware físico não foi implementada.
- Sem `.env` configurado (veja "Configuração"), nada roda — nem a API, nem o chatbot.

## Equipe

Pedro Sampaio, Raul Sampaio, Lucas Garcia, Luan de Araujo, Kevin Rodrigues — EV Challenge 2026, GoodWe / FIAP.
