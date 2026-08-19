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
   integrado em modo sandbox"** — o gateway é simulado (sandbox Mercado
   Pago), dizer só "processado" sem qualificar soa como produção real.
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

**FALA:** "O primeiro pilar é o cérebro do sistema: o balanceamento de carga
entre estações. (MOSTRAR: dashboard com as estações ativas, a distribuição
de carga, e passe o mouse pelos gráficos de demanda e geração solar — os
dois respondem com tooltip mostrando a hora e o valor exato) Quando várias
estações estão em uso, o sistema redistribui a energia em tempo real,
comunicando cada limite de potência no padrão aberto OCPP — o mesmo idioma
que carregadores comerciais reais falam. E a tarifa já reage à previsão de
geração solar do dia, dando desconto pro motorista que carrega no horário
de mais sol."

**Terceira revisão**: cortada a comparação "o mesmo princípio das
operadoras reais do mercado, como a Driivz" — não é sobre não confiar no
fato, é que citar concorrente em cima do nosso próprio pilar mais forte
divide a atenção de quem assiste e não ajuda a vender o nosso sistema.
Cortado direto, não como "se passar do tempo" — o julgamento aqui é que a
frase enfraquecia mais do que ajudava, independente do cronômetro.

## 1:15 – 1:50 | Pilar 2 — Sistema de cobrança das recargas (35s)

**FALA:** "O segundo pilar é a cobrança. (MOSTRAR: tela de simulação de
pagamento / tarifação, e o totem pedindo placa + PIN) O ChargeGrid calcula
o valor por energia consumida, com tarifação dinâmica que varia por
horário, ocupação e até previsão de sol — assim como fazem redes reais tipo
Tesla e EVgo. O pagamento passa por um gateway integrado em modo sandbox, e
a conta do motorista é protegida por placa mais PIN de 4 dígitos, com hash
de segurança seguindo boas práticas de LGPD."

## 1:50 – 2:25 | Pilar 3 — Recarga inteligente + interface do usuário (35s)

**FALA:** "O terceiro pilar é a experiência de quem usa — e é aqui que mora
um dos nossos maiores diferenciais. (MOSTRAR: totem, app do motorista e o
chatbot respondendo uma pergunta) Temos três interfaces conectadas ao mesmo
motor: totem, app do motorista e dashboard de gestão. E o assistente não é
um bot de resposta pronta — é uma inteligência artificial de verdade, que
entende a pergunta, sabe o que está acontecendo no sistema agora, e ainda
tira dúvida geral sobre carro elétrico."

**Terceira revisão**: essa parte ganhou peso — o time decidiu que o
chatbot é o maior diferencial do sistema, junto com o caminho de hardware
físico que vem no fechamento, então a fala deixou de tratar o assistente
como "mais uma tela" e passou a nomear ele como diferencial de propósito.
Atenção no checklist: a pergunta que aparecer no vídeo precisa ser uma que
o chat responde bem, ver abaixo.

## 2:25 – 2:45 | Diferencial e maturidade do projeto (20s)

**FALA:** "Diferente de um protótipo de papel, o ChargeGrid já está no ar:
banco de dados em nuvem, API funcionando, 53 testes automatizados, deploy
testado — e já passou por uma auditoria de segurança de verdade, incluindo
uma falha real de autorização que a gente encontrou e corrigiu antes de
qualquer banca ver. Esse é o nosso principal diferencial — não é uma
ideia, é um sistema rodando de ponta a ponta, testado e seguro, pronto pra
evoluir."

**Terceira revisão**: tirado o `(MOSTRAR: código/terminal/deploy)` — a
banca não quer ver código ou terminal, quer ver o sistema funcionando. O
número (53 testes, deploy testado) já prova maturidade só de ser
**falado** com confiança; não precisa de tela de código pra sustentar.
Continue mostrando o sistema de verdade (a tela que já estava aberta do
Pilar 3) em vez de cortar pra outra coisa aqui.

## 2:45 – 3:00 | Próximos passos + fechamento (15s)

**FALA:** "Já temos a tarifa reagindo à previsão de sol e o balanceamento
de carga falando o padrão aberto OCPP — alinhados com o próprio DNA da
GoodWe. Os próximos passos: um cliente OCPP real conversando com hardware
de verdade, e o sensor físico de ocupação de vaga. ChargeGrid Intelligence:
gestão de recarga pronta pra escalar. Obrigado."

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
- [ ] Gravar em ambiente silencioso, câmera/tela em boa resolução
