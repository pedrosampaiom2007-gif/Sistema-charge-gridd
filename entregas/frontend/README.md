# ChargeGrid Intelligence — Dashboard

Estrutura do projeto:

```
project/
├── backend/
│   ├── ev_chargegrid.py   ← código original do Raul, sem nenhuma alteração
│   ├── api_server.py      ← camada Flask que expõe as funções do Raul via HTTP/JSON
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## Por que existe o `api_server.py`

O `ev_chargegrid.py` original é um programa de console (`input()`/`print()`).
Um navegador não consegue chamar isso diretamente. O `api_server.py`:

- **Não altera nenhuma regra de negócio** do Raul — só importa o módulo e chama
  as mesmas funções (`iniciar_sessao`, `simular_tempo`, `criar_pagamento_sandbox`,
  `balancear_carga` etc.), trocando `input()`/`print()` por request/response JSON.
- Mantém o **mesmo processo Python rodando**, porque `potencia_kw` de cada
  estação só existe na memória (não é salvo no `chargegrid.db`) — então o
  dashboard só consegue mostrar kW em tempo real se falar com esse processo
  vivo, e não só com o banco.

⚠️ **Combine com o Raul antes de mesclar**: se ele (ou outra pessoa do grupo)
já estiver criando uma API separada, alinhem para não terem dois servidores
fazendo a mesma coisa. Se ele preferir manter só o script de console, este
`api_server.py` pode virar a própria entrega da "camada de API" do grupo.

## Como rodar

**1. Backend (API):**
```bash
cd backend
pip install -r requirements.txt
python api_server.py
```
Sobe em `http://localhost:5000`. Ele já popula o `chargegrid.db` com as 4
placas de teste (ABC1D23, XYZ9F88, GHI3K45, DEF7M01) na primeira execução.

**2. Frontend:**
Abra `frontend/index.html` direto no navegador (duplo clique), ou sirva com:
```bash
cd frontend
python -m http.server 5500
```
e acesse `http://localhost:5500`.

Se o backend rodar em outro host/porta, mude a constante `API_BASE` no topo
de `frontend/app.js`.

## O que o dashboard faz

- Painel com as 10 estações: status (Ocupada/Livre), ponteiro de potência (kW),
  kWh consumidos, valor da sessão, método de pagamento.
- Botão para **iniciar sessão** (pede placa, hora, pagamento — valida contra
  o `validar_usuario` do Raul) e **encerrar sessão** (chama
  `criar_pagamento_sandbox` + `confirmar_pagamento`, mostra o valor cobrado).
- KPIs: faturamento do dia, sessões do dia, estações ativas, consumo total.
- Medidor de potência da rede (soma das estações / limite de 50 kW do DLB).
- Gráfico da curva de demanda prevista pela IA (24h), com marcador na hora atual.
- Atualização automática a cada 4 segundos via polling (`fetch`).

## Atualizações (rodada 2 — checagem de requisitos)

- **Consumo/receita em tempo real:** o `api_server.py` agora roda um loop
  automático em background (`_loop_simulacao`) que chama `cg.simular_tempo()`
  a cada `SIMULACAO_INTERVALO_SEGUNDOS` (15s reais = 30min simulados) sempre
  que há estação ativa. Antes disso, kWh/valor só subiam se alguém chamasse
  a função manualmente — agora sobe sozinho, como um sistema de verdade.
- **Pico previsto no gráfico:** `app.js` agora calcula e marca visualmente
  o horário de maior demanda prevista (círculo âmbar + rótulo "Pico Xh · Y%"),
  além da hora atual (linha tracejada azul).
- **5ª função de leitura oficial:** adicionei `obter_potencia_estacoes()` ao
  final de `ev_chargegrid.py` (só uma função nova, nenhuma linha das
  originais do Raul foi tocada). O `/api/painel` agora monta os dados
  combinando as leituras oficiais (`listar_sessoes_ativas`,
  `obter_status_estacoes`, `obter_potencia_estacoes`) em vez de acessar os
  objetos em memória diretamente — exceto `hora_inicio`, que ainda não tem
  uma função de leitura oficial (sinalizado com comentário no código).

## Limitações conhecidas (do backend original, não corrigidas aqui)

- `potencia_kw` não é persistido no banco — se o servidor da API reiniciar,
  as estações voltam a mostrar 0 kW até uma nova sessão ser iniciada (o
  histórico de kWh/valor no banco continua intacto).
- `demonstracao_comercial()` do script original zera o estado em memória no
  final, mas não atualiza `ativa=0` no banco para as sessões 2, 3 e 4 —
  por isso o dashboard não chama essa função automaticamente.
- O intervalo do loop automático (15s = 30min simulados) é arbitrário, pensado
  pra demonstração ficar visível rápido. Para uma "simulação realista" de
  verdade, ajustem `SIMULACAO_INTERVALO_SEGUNDOS` em `api_server.py`.
