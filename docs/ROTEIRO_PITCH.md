# Roteiro — Vídeo Pitch ChargeGrid Intelligence

GoodWe EV Challenge 2026 | Duração alvo: 3:00 | Entrega: 28/ago 23h59

Formato: leia o texto normalmente. Quando aparecer `(MOSTRAR: ...)`, é o
momento de cortar pra tela gravada do sistema — a fala continua por cima ou
retoma logo depois, sem pausa longa.

## O que foi corrigido nesta versão (leia antes de gravar)

Comparado com a primeira versão do roteiro, quatro coisas mudaram porque não
batiam com o sistema real, ou porque o sistema evoluiu desde que o texto foi
escrito:

1. **"O pagamento é processado por um gateway integrado"** virou **"gateway
   integrado em modo sandbox"** — o gateway é simulado: gera um ID de
   transação fake (`SIM-...`), sem gateway real por trás. Dizer só
   "processado" sem qualificar soa como produção real.
2. **"autenticação do motorista é feita por placa"** virou **"placa mais PIN
   de 4 dígitos"** — isso é uma correção que deixa o roteiro **mais forte**,
   não mais fraco: o sistema evoluiu pra exigir PIN depois que a versão
   anterior do roteiro foi escrita.
3. **Pilar 1 (demanda)** ganhou duas linhas novas, porque os dois recursos
   descritos como "próximo passo" no fechamento **já foram implementados**:
   o balanceamento de carga agora fala o protocolo aberto OCPP de verdade
   (mensagem `SetChargingProfile`), e a tarifa já reage a uma previsão real
   de geração solar (API pública Open-Meteo), com desconto automático na
   janela de mais sol.
4. **O fechamento (próximos passos)** foi reescrito porque dizia "queremos
   conectar à energia solar" como desejo — isso não é mais verdade, já
   fizemos a primeira versão. Os próximos passos reais agora são outros:
   acesso à API real da GoodWe e o sensor físico.

Também vale saber, mesmo sem entrar no vídeo por tempo: em fevereiro de 2026
a ANEEL aprovou o primeiro piloto regulatório de V2G do Brasil (Equatorial
Alagoas), testando exatamente "tarifa inteligente + solar + bateria" — a
mesma tese do ChargeGrid. Fica ótimo como resposta se a banca perguntar
"por que tarifa dinâmica importa" — ver `docs/GOODWE_ROADMAP.md` pra fonte e
detalhe. Não forcei essa frase no roteiro porque o fechamento já está no
limite de tempo; se sobrar fôlego na gravação, pode entrar como legenda na
tela em vez de fala.

### Segunda revisão — três coisas mudaram de novo

1. **Fechamento**: tirado "acesso real à API da GoodWe" da lista de
   próximos passos — os organizadores do desafio já confirmaram que não
   vão liberar. Ficaram só os dois passos que não dependem disso (cliente
   OCPP real, sensor físico).
2. **Diferencial e maturidade**: contagem de testes trocada de "mais de
   50" pra **53** (número exato — mais crível que arredondado), e ganhou
   uma frase concreta sobre a auditoria de segurança real (achamos e
   corrigimos uma falha de autorização de verdade antes de qualquer banca
   ver, não é só "revisamos o código").
3. **Pilar 1**: a dica de `(MOSTRAR: ...)` agora pede pra passar o mouse
   nos gráficos durante a gravação — os dois (demanda e geração solar) já
   respondem a hover com tooltip mostrando a hora e o valor exato. É um
   detalhe de acabamento que fica bem na câmera e não custa segundo
   nenhum de fala.

**Dados de teste já populados pro vídeo** (10 placas, sessões pagas no
histórico, 3 estações ocupadas de verdade, 1 em manutenção) — ver
`docs/DADOS_TESTE.md` pra login exato de cada tela e sugestão de ordem de
gravação que aproveita esses dados sem precisar cadastrar nada na hora.

### Quinta revisão — tecnologias nomeadas + tarifa como diferencial explícito

1. **Tecnologias citadas** (superficial, sem parar pra explicar nenhuma):
   machine learning (Pilar 1, previsão de demanda), Open-Meteo (Pilar 1,
   fonte da previsão solar), Groq (Pilar 3, o modelo de linguagem por trás
   do chat), Python e Postgres (maturidade, back-end e banco em nuvem).
   Objetivo é só ancorar que cada peça do sistema é tecnologia real e
   nomeável, não inventar tempo de fala novo explicando cada uma.
   **Correção**: a primeira versão desta revisão citava "gateway do Mercado
   Pago" no Pilar 2 — errado. `USAR_API_REAL_MERCADOPAGO` existe no código
   mas fica `False` por padrão; o pagamento simulado que roda de verdade
   (`criar_pagamento_sandbox`) nunca chama a API da Mercado Pago, só gera
   um ID de transação fake. O que aparece de verdade na tela são os
   métodos PIX / Cartão / App / QR code — voltei o Pilar 2 pra citar isso
   em vez de um gateway que não roda no sistema.
2. **Pilar 1 e 2**: "horário de pico" virou "horário de pico **da rede**" /
   "**real** da rede" — reflete a correção que fizemos na lógica da tarifa
   (`ev_chargegrid.ia_calcular_tarifa`): antes, meio-dia também contava como
   pico só pela demanda de almoço nas estações, cobrando duas vezes pelo
   mesmo motivo e nunca deixando o meio-dia pegar desconto solar de
   verdade. Agora pico é só o horário de ponta real da rede elétrica —
   coerente com a frase que já estava no roteiro ("a mesma ideia de tarifa
   inteligente que reage à disponibilidade solar que a GoodWe já promove
   com o app SEMS", ver `docs/GOODWE_ROADMAP.md`), que antes da correção
   era descrição e comportamento **diferentes** do sistema no horário que
   mais importa.
3. **Cortado "assim como fazem redes reais tipo Tesla e EVgo" do Pilar 2**
   — mesmo raciocínio da Terceira revisão que já tinha cortado a
   comparação com a Driivz no Pilar 1: citar concorrente em cima do nosso
   diferencial mais forte divide atenção, não ajuda a vender. O espaço
   liberado virou a frase mais precisa sobre horário de pico real.
4. **No sistema, não só no roteiro**: totem e dashboard agora mostram um
   aviso "⚡ horário de ponta da rede" (cor âmbar) quando o pico está
   ativo, distinto visualmente do desconto de madrugada/solar (cor cyan) —
   antes disso só existia o aviso de desconto, sem indicar quando a tarifa
   está mais cara e por quê. Então quem grava (ou quem testar o sistema ao
   vivo na banca) vê o mesmo diferencial que o roteiro descreve, não só
   ouve sobre ele.
5. **Orçamento de tempo**: as mudanças acima somam poucas palavras por
   pilar (a maior parte foi substituição, não adição pura — cortar
   Tesla/EVgo pagou a maior parte do texto novo). Ainda assim, **cronometre
   de novo antes de gravar** (já era item do checklist abaixo). Se passar
   de 3:00, corte primeiro o item 1 desta revisão (os nomes de tecnologia
   são reforço, não essenciais) antes de mexer nos 3 pilares principais.

### Sexta revisão — só Pix tem tela ao vivo, e o benefício pra empresa

1. **Pilar 2: "PIX, cartão, app ou QR code" virou só "via Pix"**. Motivo:
   o totem tem 4 botões de método de pagamento, mas só um fluxo de
   confirmação existe de verdade — a tela de pagamento (`screen-pagamento`
   em `entregas/files/index.html`) tem o texto fixo "Escaneie para pagar
   via Pix" e gera um QR code real (biblioteca `QRCode`), **sempre**,
   não importa qual botão foi clicado antes. Cartão/App/QR Code são
   rótulos que ficam salvos na sessão (aparecem no histórico, no
   relatório), mas não têm tela própria — gravar qualquer um deles ainda
   mostraria a tela do Pix, o que ia contradizer a fala. `metodoSelecionado
   = "PIX"` já é o padrão do totem, então não precisa nem trocar nada na
   gravação — só não selecionar outro chip antes de encerrar a sessão.
2. **Benefício pra empresa, não só pro motorista**: o roteiro descrevia
   cashback e tarifa como coisa boa pro motorista, mas quem decide comprar
   a plataforma é o estabelecimento (shopping, posto, condomínio) — o
   cashback vira argumento de venda pra ele: fideliza cliente e traz
   recorrência pro local que tem as estações, não só desconto avulso.
   Ligado direto ao modelo de receita (88% fica com o estabelecimento, ver
   `docs/BUSINESS_MODEL.md`): mais gente voltando pra carregar é mais
   receita pra quem investiu na infraestrutura.
3. **Tempo**: item 1 troca "PIX, cartão, app ou QR code" (7 palavras) por
   "via Pix" (2) e corta a frase de hash/LGPD (8 palavras) — economia de
   ~13 palavras. Item 2 (cashback/fidelização) usa umas 20 palavras. Saldo
   líquido de +7 palavras no Pilar 2 (~3-4s nesse ritmo de fala) — dentro
   do que a cronometragem de teste (checklist) deve pegar se passar do
   limite; se precisar cortar, tire a frase de cashback antes da de
   tarifa/pico, que é o pilar técnico mais forte do vídeo.

---

## 0:00 – 0:15 | Gancho / Problema (15s)

**FALA:** "O Brasil já tem mais de 500 mil veículos elétricos e plug-in
rodando — mas a rede de recarga não cresce no mesmo ritmo. Hoje são quase 20
carros pra cada ponto de recarga público. Pra empresas que operam estações
comerciais, isso significa um problema real: como gerenciar demanda,
cobrança e experiência do usuário ao mesmo tempo, sem virar caos?"

*(sem alteração — números de mercado, não afirmação sobre o nosso sistema)*

## 0:15 – 0:35 | Apresentação da solução (20s)

**FALA:** "Esse é o ChargeGrid Intelligence — uma plataforma de gestão
inteligente de recarga comercial de veículos elétricos, feita pela nossa
equipe pro desafio GoodWe. (MOSTRAR: tela inicial do totem ou do dashboard,
com o nome do projeto) Ela resolve os três pilares que uma operação de
recarga comercial precisa: gestão de demanda, cobrança e experiência do
usuário — tudo rodando em nuvem, de verdade, não só no papel."

*(sem alteração)*

## 0:35 – 1:15 | Pilar 1 — Gerenciamento inteligente da demanda de potência (40s)

**FALA:** "O primeiro pilar é o cérebro do sistema: previsão de demanda com
machine learning e balanceamento de carga entre estações. (MOSTRAR: dashboard
com as estações ativas, a distribuição de carga, e passe o mouse pelos
gráficos de demanda e geração solar — os dois respondem com tooltip
mostrando a hora e o valor exato) O sistema redistribui a energia em tempo
real, falando o padrão aberto OCPP — o mesmo idioma que carregadores
comerciais reais falam. E a tarifa reage a dois sinais reais: horário de
pico da rede e geração solar prevista pela Open-Meteo, com desconto pro
motorista que carrega no horário de mais sol."

**Terceira revisão**: cortada a comparação "o mesmo princípio das
operadoras reais do mercado, como a Driivz" — não é sobre não confiar no
fato, é que citar concorrente em cima do nosso próprio pilar mais forte
divide a atenção de quem assiste e não ajuda a vender o nosso sistema.
Cortado direto, não como "se passar do tempo" — o julgamento aqui é que a
frase enfraquecia mais do que ajudava, independente do cronômetro.

## 1:15 – 1:50 | Pilar 2 — Sistema de cobrança das recargas (35s)

**FALA:** "O segundo pilar é a cobrança. (MOSTRAR: totem gerando o QR code
de pagamento via Pix, e pedindo placa + PIN) O ChargeGrid calcula o valor
por energia consumida, com tarifação dinâmica ligada ao horário de pico
real da rede, à ocupação das estações e à previsão de geração solar do
dia. O pagamento é simulado em modo sandbox via Pix, e a conta do
motorista é protegida por placa mais PIN de 4 dígitos. Todo motorista
ainda ganha 5% de cashback carregando pela ChargeGrid — fideliza cliente e
traz recorrência pra quem opera as estações."

## 1:50 – 2:25 | Pilar 3 — Recarga inteligente + interface do usuário (35s)

**FALA:** "O terceiro pilar é a experiência de quem usa. (MOSTRAR: totem,
app do motorista e o chatbot respondendo uma pergunta) Temos três
interfaces conectadas ao mesmo motor: totem, app do motorista e dashboard
de gestão. E o assistente não é um bot de resposta pronta — é uma
inteligência artificial de verdade rodando via Groq, que entende a
pergunta, sabe o que está acontecendo agora, e ainda tira dúvida geral
sobre carro elétrico."

**Quarta revisão**: tirado "é aqui que mora um dos nossos maiores
diferenciais" — quem é diferente não precisa dizer que é diferente, só
mostrar funcionando. O chatbot continua sendo o ponto mais forte do vídeo,
só que agora prova isso pela demonstração (MOSTRAR) e pela descrição do
que ele faz de verdade, não por um rótulo colado na frase. Atenção no
checklist: a pergunta que aparecer no vídeo precisa ser uma que o chat
responde bem, ver abaixo.

## 2:25 – 2:45 | Diferencial e maturidade do projeto (20s)

**FALA:** "Diferente de um protótipo de papel, o ChargeGrid já está no ar:
banco de dados Postgres em nuvem, back-end em Python, 53 testes automatizados, deploy
testado — e já passou por uma auditoria de segurança de verdade, incluindo
uma falha real de autorização que a gente encontrou e corrigiu antes de
qualquer banca ver."

**Terceira e quarta revisão**: tirado o `(MOSTRAR: código/terminal/deploy)`
— a banca não quer ver código ou terminal, quer ver o sistema funcionando;
continue na tela do Pilar 3 em vez de cortar pra outra coisa. Também tirado
"esse é o nosso principal diferencial — não é uma ideia..." no final da
fala: são os próprios números (53 testes, deploy testado, falha real
corrigida) que provam maturidade — dizer "somos diferentes" depois de já
ter mostrado os fatos só repete o que os fatos já disseram sozinhos, e
gasta tempo à toa.

## 2:45 – 3:00 | Próximos passos + fechamento (15s)

**FALA:** "Já temos a tarifa reagindo à previsão de sol e o balanceamento
de carga falando o padrão aberto OCPP — alinhados com o próprio DNA da
GoodWe. E o próximo passo já está em andamento: o sensor físico de
ocupação, ESP32 com sensor ultrassônico, com firmware e endpoint da API já
validados em simulação real — a montagem física é a etapa seguinte. É
isso que vai levar o ChargeGrid ainda mais longe. ChargeGrid Intelligence:
gestão de recarga pronta pra escalar. Obrigado."

**Quarta revisão**: o fechamento ficou mais claro sobre o hardware físico
ser o que empurra o projeto além do que já está pronto — "está em
andamento" e "a nossa própria equipe está montando agora" deixam explícito
que não é só uma ideia na lista, é trabalho real acontecendo em paralelo
(o Raul e o Luan). É aqui, não no meio do vídeo, que faz sentido apontar
pra frente — o resto do roteiro mostra o que já está pronto, o fechamento
mostra pra onde vai.

**Sétima revisão — "montando agora" virou "validado em simulação"**: pedido
pra checar se o sensor físico é viável antes de prometer no vídeo. Resposta:
tecnicamente sim — é o mesmo ESP32 + sensor ultrassônico (HC-SR04) que o
próprio material de dicas do desafio (`PCP - Extra - Challenge GoodWe
Dicas.pdf`, do professor Alexandre Russi Jr.) recomenda em tutorial
("Monitorando consumo de energia com ESP32"), e o endpoint que o firmware
vai chamar (`POST /api/estacoes/<n>/telemetria`) já existe e está pronto,
documentado em `docs/TAREFAS_EQUIPE.md`. O que não dá pra garantir é que a
montagem física — comprar peça, montar, resolver Wi-Fi instável — termine
a tempo da entrega de 28/ago: faltam só 8 dias (hoje é 20/ago), e o próprio
`docs/TAREFAS_EQUIPE.md` já previu esse risco, com um plano B explícito:
"o Wokwi sozinho já mostra o conceito funcionando... terminar a simulação e
deixar a montagem física pra depois da entrega é uma opção real, não um
fracasso." Por isso o fechamento agora promete só o que dá pra garantir sem
depender de frete ou sorte de fiação: circuito + firmware validados em
simulação (Wokwi), API pronta esperando o hardware. Se Raul e Luan já
tiverem montado fisicamente até a gravação, é só trocar "validados em
simulação real" por "montado e testado" — mais forte ainda, e continua
verdade.

**Histórico**: a primeira versão do roteiro dizia "queremos conectar à
energia solar" como desejo — trocamos porque já implementamos. A segunda
versão dizia "acesso real à API da GoodWe" como próximo passo — trocamos
de novo porque os organizadores já confirmaram que isso não vai acontecer
nesta rodada (ver `docs/GOODWE_ROADMAP.md`). Os dois passos que sobraram
(cliente OCPP real, sensor físico) continuam sendo trabalho futuro de
verdade, sem depender de nada externo — ver `docs/TAREFAS_EQUIPE.md`.

---

## Checklist antes de gravar

- [ ] Confirmar que o deploy está online e estável no dia da gravação
      (checar `GET /api/painel` e `GET /api/solar` respondendo, não só a
      tela abrindo — o Render em plano gratuito hiberna e a primeira
      chamada depois de um tempo parado pode falhar uma vez antes de
      responder)
- [ ] Login e placas pra usar na gravação já estão em `docs/DADOS_TESTE.md`
      — não precisa cadastrar nada na hora, o dashboard já abre com dado
      de verdade (estações ocupadas, faturamento, histórico populado)
- [ ] Testar o chatbot com a pergunta que vai aparecer no vídeo (evitar
      resposta errada ao vivo) — **evite perguntar sobre faturamento ou
      receita durante a demonstração do app/totem**: desde a revisão de
      segurança, o chat só responde dado de negócio quando logado como
      admin, então essa pergunta especificamente daria uma resposta de
      recusa no ar, o que é o comportamento CERTO mas pode confundir quem
      assiste sem contexto. Perguntas sobre disponibilidade de estação ou
      dúvida geral de carro elétrico mostram o chat bem.
- [ ] Cronometrar uma leitura teste — se passar de 3:00, cortar primeiro o
      Pilar 3 ou a maturidade, nunca os 3 pilares principais (valem 45 dos
      100 pontos). O Pilar 1 cresceu nesta revisão — é o primeiro lugar pra
      olhar se passar do tempo.
- [ ] Confirmar com Raul e Luan o status real do sensor físico antes de
      gravar o fechamento — se a montagem física já estiver pronta e
      testada, trocar "validados em simulação real" por "montado e
      testado" no Pilar de fechamento (ver Sétima revisão)
- [ ] Gravar em ambiente silencioso, câmera/tela em boa resolução
