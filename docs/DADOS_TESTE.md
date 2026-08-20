# Dados de teste — pra gravar o vídeo

Credenciais e placas já cadastradas no banco de produção (Supabase, o mesmo
que o Render usa) — tudo pronto pra abrir as telas e já aparecer rico, sem
precisar cadastrar nada na hora da gravação.

**Troque a senha do admin e os PINs antes de expor o sistema publicamente
de verdade** — esses valores estão documentados aqui de propósito, pra
facilitar o teste da equipe; não são segredo.

<br>

## Login do administrador (dashboard)

| Campo | Valor |
|---|---|
| Usuário | `admin` |
| Senha | `chargegrid2026` |

<br>

## Placas cadastradas (10 no total — todas com PIN `0000`)

| Placa | Nome | Situação no momento em que este doc foi escrito |
|---|---|---|
| `ABC1D23` | Cliente Executivo A | Sessão **ativa** — Estação 1 |
| `XYZ9F88` | Frota Corporativa B | Sessão **ativa** — Estação 2 |
| `GHI3K45` | Cliente Shopping C | Sessão **ativa** — Estação 3 |
| `DEF7M01` | Usuário Demo D | Livre, sem sessão no momento |
| `JKL4M56` | Maria Oliveira | Tem sessão paga no histórico (12h, fora de pico — demanda de almoço, não horário de ponta, PIX) |
| `NOP7Q89` | João Pereira | Tem sessão paga no histórico (3h, madrugada/desconto, Cartão) |
| `RST1U23` | Ana Costa | Tem sessão paga no histórico (13h, janela solar/desconto, App) |
| `VWX5Y67` | Carlos Souza | Tem sessão paga no histórico (19h, pico noturno, QR Code) |
| `ZAB8C90` | Fernanda Lima | Tem sessão paga no histórico (9h, fora de pico, PIX) |
| `CDE2F34` | Bruno Alves | Tem sessão paga no histórico (15h, janela solar, Cartão) |

Todas as **6 últimas** (Maria a Bruno) foram cadastradas e tiveram sessão
paga geradas via API de propósito, pra popular o dashboard com faturamento,
sessões e consumo diferentes de zero, e pro histórico de pagamento do app
do motorista não aparecer vazio se você logar com qualquer uma delas — bom
material pra `(MOSTRAR: app do motorista)` no roteiro.

<br>

## Estado das estações (no momento em que este doc foi escrito)

| Estação | Status | O que mostrar |
|---|---|---|
| 1, 2, 3 | **Ocupada** | Sessões reais rodando (kWh e valor subindo sozinhos a cada ~15s) — bom pra mostrar o painel "vivo" |
| 4 | **Manutenção** | Motivo: "Cabo de recarga em revisão" — bom pra demonstrar essa funcionalidade específica |
| 5–10 | **Livre** | De propósito — é aqui que dá pra demonstrar **ao vivo** o fluxo de iniciar uma recarga nova durante a gravação, sem atrapalhar o que já está populado |

Esse estado é dinâmico — se alguém mexer no sistema entre agora e a
gravação (ou se o Render reiniciar e essas 3 sessões ativas ficarem
"velhas" com muito kWh acumulado), é só usar o dashboard normalmente pra
ajustar: **Encerrar sessão** numa das ativas e **Iniciar sessão** de novo
com uma das placas acima, se quiser números mais "frescos" pro vídeo.

<br>

## Roteiro de gravação sugerido pra aproveitar esses dados

1. **Totem** (`entregas/files/index.html`): mostrar uma placa livre (ex: `DEF7M01`) iniciando uma recarga nova — mostra o fluxo completo + a nota de tarifa (madrugada ou solar, dependendo da hora real).
2. **App do motorista** (`entregas/app/index.html`): logar com `JKL4M56` / PIN `0000` — o histórico já aparece populado, dá pra mostrar o assistente respondendo sobre o gasto pessoal.
3. **Dashboard** (`entregas/frontend/index.html`): logar com `admin` / `chargegrid2026` — grid já mostra 3 estações ocupadas + 1 em manutenção lado a lado, KPIs com número de verdade, e os dois gráficos (demanda e geração solar) já respondem a hover com tooltip mostrando hora + valor exato.
4. Se quiser mostrar a funcionalidade de manutenção ao vivo (em vez de só a estação 4 já pronta), tirar a estação 4 da manutenção primeiro (**Sair da manutenção**) e colocar de novo na frente da câmera.
