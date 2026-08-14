# ⚙️ Instalação e Configuração — ChargeGrid Intelligence

## Configuração (só na primeira vez)

Crie um arquivo `.env` na raiz do repositório (mesmo nível do README) com:
```
DATABASE_URL=postgresql://usuario:senha@host:porta/postgres
GROQ_API_KEY=gsk_...
```
Esse arquivo **nunca é commitado** (está no `.gitignore`, de propósito — tem senha de banco e chave de API). `DATABASE_URL` é a connection string do Supabase (use o modo **Session pooler**, não o "Direct connection" — o direct costuma resolver só em IPv6 e falha em várias redes). `GROQ_API_KEY` vem em console.groq.com → API Keys.

<br>

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

**Se der "o sistema não pode encontrar o caminho especificado"**, o Python está instalado mas o comando `python` não foi para o PATH. Use `py` no lugar de `python` em todos os comandos deste guia (`py --version`, `py api_server.py`, `py -m unittest ...`) — o `py` é o inicializador que o instalador do Windows sempre registra.

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

Confirme que existe um arquivo `.env` na **raiz do repositório** (um nível acima de `entregas/`, mesmo nível do README) com `DATABASE_URL` e `GROQ_API_KEY` preenchidos — veja a seção "Configuração" acima se ainda não criou. Sem isso, o próximo passo falha na hora.

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
- **Totem** — `entregas/files/index.html`: digite uma placa de teste (`ABC1D23`, `XYZ9F88`, `GHI3K45` ou `DEF7M01`) pra simular uma recarga. Pra testar uma estação específica em vez da 1, adicione `?estacao=3` no final do endereço, na barra do navegador (troque o número). Abaixo do botão "Iniciar recarga" aparece a tarifa do momento — entre 0h e 6h ela mostra desconto de madrugada.
- **App do motorista** — `entregas/app/index.html`: login com uma das placas de teste acima **e o PIN `0000`** (PIN de teste de todas as 4 contas — troque antes de uma apresentação real) — mostra histórico de pagamentos e o chat.
- **Dashboard (gestor)** — `entregas/frontend/index.html`: login com `admin` / `chargegrid2026` (senha de teste — troque antes de uma apresentação real). Em cada estação livre tem um link "Colocar em manutenção" (some enquanto a estação está ocupada); e um botão "Baixar relatório do dia" no topo da lista de estações baixa um `.txt` com o resumo do dia.

### 9. Testar a API direto, sem interface (mais rápido pra conferir um endpoint isolado)

No **segundo terminal** (passo 7):

**Ver o painel das 10 estações:**
```powershell
curl.exe http://127.0.0.1:5000/api/painel
```

**Iniciar uma sessão de recarga** (estação 2, placa `ABC1D23`, 14h, Pix):
```powershell
$body = @{ estacao = 2; usuario = "ABC1D23"; hora = 14; pagamento = "PIX" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/sessoes/iniciar" -Method POST -ContentType "application/json" -Body $body
```
Repare que o `POST` usa `Invoke-RestMethod`, não `curl.exe -X POST -d ...` — no PowerShell, `curl` (sem `.exe`) é só um apelido de `Invoke-WebRequest` e a forma de escapar aspas dentro de `-d` varia por versão do Windows e costuma falhar silenciosamente com "Bad Request"; `Invoke-RestMethod` evita esse problema por completo.

**Encerrar a sessão que acabou de abrir (gera o recibo simulado):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/sessoes/2/encerrar" -Method POST
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

São 32 testes cobrindo tarifação dinâmica, balanceamento de carga (DLB), hash/mascaramento de placa (LGPD), a correção da demo comercial, a busca do chatbot (que trazia dado de receita pra pergunta sobre bateria) e a fronteira de acesso do chat (o padrão não pode enxergar faturamento) — sem escrever no Postgres de verdade (o banco é mockado nesses testes):
```powershell
cd "C:\Users\pedro\PycharmProjects\Sistema-charge-gridd"
python -m unittest discover -s entregas/tests -v
```
Esperado: `OK` na última linha, com cada teste listado como `ok` acima.

### 12. Encerrar tudo

Volte no terminal da API (passo 6) e aperte `Ctrl+C` pra derrubar o servidor. Feche as janelas de terminal normalmente.

---

Se a API rodar em outro host/porta (não `127.0.0.1:5000`), ajuste a constante `API_BASE` no topo de cada `app.js` (totem, dashboard, app). Ela aponta pra `127.0.0.1` e não pra `localhost` de propósito: no Windows, `localhost` resolve primeiro pra IPv6, o Flask escuta em IPv4, e cada chamada perde ~1,8s tentando o endereço errado — com a tela consultando a API a cada 3s, isso deixava o painel permanentemente atrasado.
