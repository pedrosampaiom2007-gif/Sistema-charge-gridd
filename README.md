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
render.yaml                           blueprint de deploy da API no Render (opcional, ver "Deploy")
entregas/
├── ev_chargegrid.py                  motor: banco, auth, contas, pagamento, DLB, IA preditiva
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

## Configuração (só na primeira vez)

Crie um arquivo `.env` na raiz do repositório (mesmo nível deste README) com:
```
DATABASE_URL=postgresql://usuario:senha@host:porta/postgres
GROQ_API_KEY=gsk_...
```
Esse arquivo **nunca é commitado** (está no `.gitignore`, de propósito — tem senha de banco e chave de API). `DATABASE_URL` é a connection string do Supabase (use o modo **Session pooler**, não o "Direct connection" — o direct costuma resolver só em IPv6 e falha em várias redes). `GROQ_API_KEY` vem em console.groq.com → API Keys.

## Como testar (passo a passo, do zero)

Instruções pra Windows com PowerShell (é o que o time usa). Em Mac/Linux o terminal se abre diferente, mas os comandos Python são os mesmos (troque `python` por `python3` se `python` não for reconhecido).

### 1. Abrir um terminal

- Aperte a tecla **Windows**, digite `PowerShell`, aperte **Enter**. Ou: abra o Explorador de Arquivos, entre na pasta do repositório, clique com o botão direito num espaço vazio e escolha **"Abrir no Terminal"** (ou "Abrir janela do PowerShell aqui").
- Você vai ver um prompt do tipo `PS C:\Users\seu-usuario>` — é ali que cada comando abaixo é digitado, seguido de Enter.

### 2. Conferir se o Python está instalado

```powershell
python --version
```
Espera-se `Python 3.9` ou mais novo. **Se abrir a Microsoft Store** em vez de mostrar uma versão, o Python não está instalado de verdade (é só um atalho do Windows) — instale em [python.org/downloads](https://www.python.org/downloads/) marcando a caixa **"Add python.exe to PATH"** durante a instalação, feche e reabra o terminal, e tente de novo.

### 3. Entrar na pasta do projeto

```powershell
cd "C:\Users\pedro\PycharmProjects\Sistema-charge-gridd"
```
(ajuste o caminho se você clonou o repositório em outro lugar)

### 4. Instalar as dependências

```powershell
cd entregas
pip install -r "requirements (1).txt"
```
As aspas em volta do nome do arquivo são obrigatórias — ele tem um espaço e um parêntese no nome, sem aspas o PowerShell entende como dois comandos diferentes e dá erro. A instalação baixa Flask, psycopg2, scikit-learn, groq etc. — demora alguns minutos na primeira vez. Se algum pacote falhar com erro de rede, rode o mesmo comando de novo (timeout de download é comum e geralmente resolve na segunda tentativa).

### 5. Conferir o `.env`

Confirme que existe um arquivo `.env` na **raiz do repositório** (um nível acima de `entregas/`, mesmo nível deste README) com `DATABASE_URL` e `GROQ_API_KEY` preenchidos — veja a seção "Configuração" logo acima se ainda não criou. Sem isso, o próximo passo falha na hora.

### 6. Subir a API — esse terminal fica ocupado, não feche

Ainda no mesmo terminal:
```powershell
cd files
python api_server.py
```
Espere aparecer algo parecido com isto (pode levar alguns segundos):
```
[IA] modelo_demanda.pkl carregado com sucesso (RandomForest, dados SP2).
 * Serving Flask app 'api_server'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```
A última linha (`Running on http://127.0.0.1:5000`) é o sinal de que a API está no ar. **Deixe essa janela aberta e rodando** — ela é o processo vivo que serve o totem, o dashboard, o app e mantém o kW de cada estação em tempo real; fechar essa janela derruba tudo. (Se aparecer `modelo_demanda.pkl não encontrado`, não é erro grave — o sistema cai pro dicionário de tarifas fixo e continua funcionando normalmente, só sem o modelo treinado.)

### 7. Abrir um SEGUNDO terminal, pra testar sem derrubar a API

Repita o passo 1 (tecla Windows → `PowerShell` → Enter) numa **janela nova** — a primeira precisa continuar aberta rodando a API. Nessa nova janela:
```powershell
cd "C:\Users\pedro\PycharmProjects\Sistema-charge-gridd"
```

### 8. Testar pelas telas, no navegador

Com a API do passo 6 rodando, abra estes arquivos direto no navegador (duplo clique no Explorador de Arquivos, ou arraste o arquivo pra uma aba do Chrome/Edge):

- **Landing page** — `entregas/index.html`: escolhe entre motorista, minha conta ou administrador.
- **Totem** — `entregas/files/index.html`: digite uma placa de teste (`ABC1D23`, `XYZ9F88`, `GHI3K45` ou `DEF7M01`) pra simular uma recarga. Pra testar uma estação específica em vez da 1, adicione `?estacao=3` no final do endereço, na barra do navegador (troque o número).
- **App do motorista** — `entregas/app/index.html`: login com uma das placas de teste acima **e o PIN `0000`** (PIN de teste de todas as 4 contas — troque antes de uma apresentação real) — mostra histórico de pagamentos e o chat.
- **Dashboard (gestor)** — `entregas/frontend/index.html`: login com `admin` / `chargegrid2026` (senha de teste — troque antes de uma apresentação real).

### 9. Testar a API direto, sem interface (mais rápido pra conferir um endpoint isolado)

No **segundo terminal** (passo 7):

**Ver o painel das 10 estações:**
```powershell
curl.exe http://localhost:5000/api/painel
```

**Iniciar uma sessão de recarga** (estação 2, placa `ABC1D23`, 14h, Pix):
```powershell
$body = @{ estacao = 2; usuario = "ABC1D23"; hora = 14; pagamento = "PIX" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/sessoes/iniciar" -Method POST -ContentType "application/json" -Body $body
```
Repare que o `POST` usa `Invoke-RestMethod`, não `curl.exe -X POST -d ...` — no PowerShell, `curl` (sem `.exe`) é só um apelido de `Invoke-WebRequest` e a forma de escapar aspas dentro de `-d` varia por versão do Windows e costuma falhar silenciosamente com "Bad Request"; `Invoke-RestMethod` evita esse problema por completo.

**Encerrar a sessão que acabou de abrir (gera o recibo simulado):**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/sessoes/2/encerrar" -Method POST
```

Se qualquer um desses comandos travar sem responder, volte no terminal do passo 6 e confira se a API ainda está rodando sem erro na tela.

### 10. Testar o chatbot

Pode ser no segundo terminal — não depende da API estar no ar (o chatbot fala direto com o Postgres):
```powershell
cd "C:\Users\pedro\PycharmProjects\Sistema-charge-gridd\entregas"
python chatbot.py
```
Faça uma pergunta sobre dado real (ex: "quantas sessões eu tive hoje?") e uma pergunta geral de carro elétrico, pra ver os dois modos de resposta funcionando. `Ctrl+C` encerra.

**Chatbot no Colab (alternativa, sem instalar nada local):** abra `ChargeGrid_Intelligence_chatbot.ipynb` no Google Colab — ele baixa os arquivos direto do GitHub, não precisa de upload manual. Configure dois "Secrets" no Colab (ícone de chave 🔑, na barra lateral): `DATABASE_URL` e `GROQ_API_KEY`, com os mesmos valores do seu `.env`.

### 11. Rodar os testes automatizados

Cobrem tarifação dinâmica, balanceamento de carga (DLB), hash/mascaramento de placa (LGPD) e a correção da demo comercial (regressão) — sem escrever no Postgres de verdade (o banco é mockado nesse teste específico):
```powershell
cd "C:\Users\pedro\PycharmProjects\Sistema-charge-gridd"
python -m unittest discover -s entregas/tests -v
```
Esperado: `OK` na última linha, com cada teste listado como `ok` acima.

### 12. Encerrar tudo

Volte no terminal da API (passo 6) e aperte `Ctrl+C` pra derrubar o servidor. Feche as janelas de terminal normalmente.

---

Se a API rodar em outro host/porta (não `localhost:5000`), ajuste a constante `API_BASE` no topo de cada `app.js` (totem, dashboard, app).

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
- **Testes automatizados** (`entregas/tests/`) cobrindo tarifação dinâmica, DLB, hash/mascaramento LGPD e a correção da demo comercial — ver "Como testar", passo 11.
- Modelo de IA preditiva (`modelo_demanda.pkl`) agora carrega de verdade também rodando pelo fluxo documentado (`cd entregas/files && python api_server.py`) — o carregamento usava caminho relativo e dependia do diretório de onde o processo era iniciado; sem isso, a API sempre caía no dicionário de tarifas fixo, mesmo com o modelo treinado disponível.
- API pronta pra deploy: porta e modo debug configuráveis por variável de ambiente (`PORT`, `FLASK_DEBUG`) e `Procfile`/`render.yaml` no repositório — ver "Deploy".
- **Revisão de segurança** (ver seção "Segurança" abaixo): rate limiting, CORS por allowlist, cabeçalhos anti-clickjacking, bloqueio de conta por tentativas de login e revogação de token no logout.
- **Cadastro de novo motorista**: antes, uma placa não reconhecida travava sem nenhum caminho pra frente — o sistema só funcionava pras 4 placas de teste. Agora dá pra se cadastrar direto no totem (quando a placa não é reconhecida na hora de iniciar a recarga) ou no app (link "Ainda não tem cadastro?" na tela de login) — os dois usam o mesmo `POST /api/usuarios`.
- **PIN de 4 dígitos** (escolhido no cadastro) protegendo o histórico de pagamento — ver "IDOR corrigido" na seção "Segurança".
- **Chat sem vazar dado de negócio pro motorista**: o assistente, quando usado de dentro da conta do motorista (placa+PIN), não revela faturamento, receita histórica nem qualquer número agregado do sistema — só o gasto pessoal daquele motorista, disponibilidade de estação, e dúvidas gerais de carro elétrico. Achado testando com um usuário real fora da equipe — ver "Segurança".

## Segurança

Revisão feita e testada nesta rodada (todos os itens abaixo foram conferidos direto na API rodando, não só lidos no código):

- **Rate limiting**: `/api/admin/login` aceita no máximo 5 tentativas por minuto por IP (`flask-limiter`) *e* bloqueia a conta por 5 minutos após 5 falhas, independente do IP de origem (cobre ataque distribuído, não só de um único IP). `/api/usuarios/<placa>/historico` tem limite de 20/min por IP contra varredura em massa de placas. Todo o resto da API tem um limite geral de 300/min por IP.
- **CORS por allowlist**: trocado o `CORS(app)` sem restrição por uma lista explícita de origens (`CORS_ORIGINS` no ambiente, com padrão cobrindo o uso local atual — inclusive `Origin: null`, que é o que o navegador manda quando os HTMLs são abertos direto como arquivo).
- **Cabeçalhos de segurança** em toda resposta: `X-Frame-Options: DENY` (clickjacking), `X-Content-Type-Options: nosniff`, `Referrer-Policy`.
- **Logout de admin de verdade**: `POST /api/admin/logout` revoga o token no servidor — antes, um token continuava válido pra sempre (até a API reiniciar) mesmo depois do usuário clicar em "Sair".
- **Sem SQL Injection**: toda consulta no motor e na API usa parâmetros (`%s` do psycopg2), nenhuma faz concatenação/f-string de SQL — auditado arquivo por arquivo (`ev_chargegrid.py`, `api_server.py`, `chatbot.py`).
- **Sem vazamento de hash/PII nas respostas**: nenhum endpoint retorna `senha_hash` nem `hash_usuario` — as respostas já usavam só a placa mascarada (LGPD), auditado endpoint por endpoint.
- **Enumeração de usuário**: o login de admin já respondia com mensagem genérica ("Usuário ou senha inválidos") tanto pra usuário inexistente quanto senha errada — nenhuma mudança necessária aí. As mensagens ligadas a placa (`Credencial não autorizada`, `já estava cadastrado`) não foram alteradas de propósito: placa não é segredo (é informação pública, visível no próprio carro), então o modelo clássico de "enumeração de usuário" não se aplica da mesma forma — o motorista *precisa* saber se a própria placa está cadastrada pra usar o totem.
- **IDOR corrigido**: `GET /api/usuarios/<placa>/historico` virou `POST /api/usuarios/historico`, exigindo a placa **e** o PIN de 4 dígitos escolhido no cadastro (`contas.pin_hash`, mesmo padrão de hash das senhas de admin). Antes, saber a placa já bastava pra ver o histórico de qualquer motorista — a placa sozinha nunca foi um segredo de verdade. `/api/usuarios/vincular` (adicionar carro à conta) também passou a exigir o PIN, fechando uma falha relacionada (antes, saber uma placa cadastrada bastava pra vincular qualquer placa nova a ela). Iniciar/encerrar sessão no totem continua só com a placa, sem PIN — não é dado sensível, e pedir PIN ali atrasaria o fluxo que precisa ser rápido.
- **Chat não vaza dado de negócio pro motorista**: `/api/chat` aceita placa+PIN opcionais; quando presentes (app do motorista), o chatbot só recebe gasto pessoal daquele motorista, disponibilidade de estação e conhecimento geral de carro elétrico — nunca faturamento, receita histórica ou qualquer dado agregado do sistema (mesma fronteira que `/api/kpis` já aplica no dashboard). Sem placa/PIN (uso interno via `chatbot.py`/notebook), o chat mantém acesso total — é a ferramenta de uso interno da equipe, não a que o cliente usa.

## Limitações conhecidas

- **O totem não tem login nem menu de navegação além do essencial** — de propósito. É um ponto de serviço físico, precisa ser rápido; funcionalidades "extras" (histórico, chat) ficam só no app do motorista, não no totem.
- A integração com hardware de carregador real (protocolo OCPP) é só simulada (a função correspondente imprime uma mensagem, não fala com equipamento nenhum) — a lógica de negócio e a interface são reutilizáveis, a comunicação com hardware físico não foi implementada.
- Sem `.env` configurado (veja "Configuração"), nada roda — nem a API, nem o chatbot.
- Sem testes automatizados para as funções que leem/escrevem no Postgres (só as pura-lógica e a demo, com o banco mockado) — cobrir isso exigiria um banco de teste descartável, que ainda não existe.
- Token de sessão do admin fica só em memória do processo da API (mesma limitação estrutural do `potencia_kw`, já documentada no código) — reiniciar a API desloga todo admin logado. O logout explícito (novo) já revoga o token antes disso, o que faltava.
- Rate limiting guarda o estado em memória do processo — um deploy com múltiplos workers/instâncias precisaria de um storage compartilhado (Redis) pra o limite valer entre eles; com 1 processo (o caso de hoje), funciona normalmente.

## Deploy (opcional)

Hoje o sistema roda em `localhost` (ver "Como testar"). O repositório já está preparado pra publicar a API num servidor de verdade, sem precisar reescrever nada:

- **`render.yaml`** (raiz do repo): blueprint do [Render](https://render.com) — aponta pra `entregas/files`, instala as dependências e sobe com `gunicorn` (servidor de produção; o servidor embutido do Flask, usado localmente, avisa explicitamente que não deve ser exposto assim).
- **`entregas/files/Procfile`**: mesma ideia, pra Railway ou qualquer host compatível com Procfile.
- Em ambos, configure `DATABASE_URL`, `GROQ_API_KEY` e `FLASK_DEBUG=0` como variáveis de ambiente no painel do serviço — nunca no código. `FLASK_DEBUG=0` é obrigatório num servidor público: com debug ligado, o Werkzeug expõe um console interativo que permite executar código remotamente.
- Depois da API publicada, troque `API_BASE` no topo de cada `app.js` (totem, dashboard, app) pra a URL pública, e sirva os HTMLs estáticos em qualquer host (GitHub Pages, Vercel, Netlify — são arquivos estáticos, não precisam de servidor Python).

Nenhuma conta é criada nem publicada automaticamente por esses arquivos — eles só deixam o repositório pronto pra quando alguém do time conectar uma conta existente (Render/Railway) e publicar.

## Equipe

Pedro Sampaio, Raul Sampaio, Lucas Garcia, Luan de Araujo, Kevin Rodrigues — EV Challenge 2026, GoodWe / FIAP.
