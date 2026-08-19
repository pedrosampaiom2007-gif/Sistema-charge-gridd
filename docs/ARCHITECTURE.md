# 🏗️ Arquitetura — ChargeGrid Intelligence

## Visão geral

O motor (`entregas/ev_chargegrid.py`) controla até 10 estações de recarga: autenticação de motorista por placa (hash SHA-256, com mascaramento em conformidade com a LGPD), balanceamento de carga entre estações ativas (DLB), tarifação dinâmica por horário e demanda, e pagamento via gateway simulado (Mercado Pago sandbox). Uma API Flask expõe esse motor para três clientes web (totem, dashboard, app do motorista) e um chatbot (rodando local ou no Colab) que responde em linguagem natural, combinando dados em tempo real com um histórico de 60 sessões reais.

**O banco de dados é Postgres na nuvem (Supabase), não um arquivo local** — qualquer processo, de qualquer computador com a credencial certa, lê e escreve no mesmo banco. **A IA do chatbot roda na nuvem (Groq)**, não localmente — não depende de instalar nem baixar modelo nenhum.

<br>

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

Todo acesso ao banco passa por `conectar()`, um pool de conexões no motor: abrir uma conexão nova no Supabase custa ~1,3s, então reaproveitar as conexões é o que faz o painel responder em ~0,3s em vez de ~5s. Leitura usa autocommit (uma ida ao banco); escrita continua transacional.

O motor é a única fonte de verdade: API, dashboard, totem, app do motorista e chatbot leem dele (direta ou indiretamente) — nenhum desses componentes duplica lógica de negócio.

<br>

## Estrutura do repositório

```
.env                                  DATABASE_URL + GROQ_API_KEY — NÃO existe no repo, veja docs/INSTALL.md
render.yaml                           blueprint de deploy da API no Render (opcional, ver docs/DEPLOY.md)
docs/
├── INSTALL.md / USER_GUIDE.md / ARCHITECTURE.md / SECURITY.md / CHANGELOG.md / DEPLOY.md
├── BUSINESS_MODEL.md                 modelo de negócio e comissão (proposta, ver ressalvas no arquivo)
├── GOODWE_ROADMAP.md                 o que já fala a língua da GoodWe hoje vs. o que uma integração real mudaria
├── ROTEIRO_PITCH.md                  roteiro do vídeo de apresentação (3:00), com o que foi corrigido e por quê
└── TAREFAS_EQUIPE.md                 divisão hardware/software da reta final, com contrato de API já pronto
entregas/
├── ev_chargegrid.py                  motor: banco, auth, contas, pagamento, DLB, IA preditiva
├── solar_optimizer.py                previsão de geração solar (Open-Meteo) e janela de desconto solar na tarifa
├── chatbot.py                        chatbot em terminal, local, sem Colab (mesma lógica do notebook)
├── dados_rag.json                    histórico de 60 sessões reais (base do RAG do chatbot)
├── modelo_demanda.pkl                modelo RandomForest treinado (previsão de demanda)
├── requirements (1).txt              dependências Python (o nome do arquivo é esse mesmo, com espaço)
├── ChargeGrid_Intelligence_chatbot.ipynb   chatbot em notebook (roda no Google Colab)
├── index.html                        landing page — escolhe motorista / minha conta / admin
├── tests/
│   └── test_ev_chargegrid.py         testes automatizados (tarifação, DLB, hash/mascaramento, regressão da demo)
├── files/                            totem do motorista (self-service) + api_server.py
│   ├── api_server.py                 camada Flask que expõe o motor via HTTP/JSON
│   ├── Procfile                      comando de start pra deploy (Render/Railway)
│   └── index.html / app.js / style.css
├── app/                              área pessoal do motorista — login por placa
│   └── index.html / app.js / style.css
└── frontend/                         dashboard do gestor — login admin
    └── index.html / app.js / style.css

modelagem_ia/
├── README.md                         o que tem dentro do zip abaixo
└── IA aplicada.zip                   notebook de treino do modelo + gráfico comparativo
```

<br>

## Fluxo principal (totem → API → banco → dashboard/app → chatbot)

1. Motorista inicia a sessão no totem → `POST /api/sessoes/iniciar` na API.
2. A API valida a placa contra o banco e grava a sessão no Postgres.
3. O dashboard (logado) e o próprio totem, que fazem polling em `GET /api/painel`, refletem a estação ocupada, o consumo e o valor acumulado.
4. Ao encerrar (`POST /api/sessoes/<n>/encerrar`), a API gera a cobrança simulada, o totem mostra o QR Pix e emite o recibo.
5. A qualquer momento, em qualquer lugar (não precisa ser no totem), o motorista abre o app, loga com a placa, e vê o histórico daquela sessão — e de qualquer outro carro vinculado à mesma conta.
6. O chatbot (local ou Colab) consulta as mesmas funções de leitura do motor, direto no Postgres — sem depender de nenhum arquivo local, sem precisar da API estar no ar.

<br>

## Solar, OCPP e telemetria de hardware

Três peças que aproximam o simulado do real, verificadas contra API antes de documentar (ver `docs/GOODWE_ROADMAP.md` pras fontes externas checadas):

- **Janela de desconto solar** (`entregas/solar_optimizer.py`) — busca a previsão de radiação solar do dia (Open-Meteo, API pública sem chave, cacheada por dia) e aplica até 10% de desconto na tarifa nas horas de maior geração prevista, desde que não seja horário de pico. Cai num perfil sintético (formato de sino, pico ao meio-dia) se a API não responder — mesma filosofia de fallback do modelo de demanda. Fica dentro de `ia_calcular_tarifa`, não numa camada separada, porque o valor cobrado de verdade (`simular_tempo`) e o valor mostrado no painel precisam vir do mesmo cálculo — senão o motorista veria um preço na tela e pagaria outro.
- **DLB falando o vocabulário OCPP 1.6J** (`ev_chargegrid.balancear_carga`) — o algoritmo de balanceamento continua sendo rateio igualitário, isso não mudou; o que mudou é que agora cada limite de potência é comunicado como uma mensagem `SetChargingProfile` real (`chargingProfileId`, `stackLevel`, `chargingProfilePurpose: TxDefaultProfile`, `chargingRateUnit: W`, `limit`), reaproveitando o `ocpp_enviar()` que já existia pras mensagens de início/fim de sessão.
- **`POST /api/estacoes/<n>/telemetria`** — contrato pronto pra um sensor físico de ocupação (ESP32 + HC-SR04) reportar presença de carro, guardado em memória (`ocupacao_fisica` em cada estação do `/api/painel`, `None` até algum hardware reportar pela primeira vez). Protegido por `TELEMETRIA_TOKEN` opcional — ver `docs/SECURITY.md`.
