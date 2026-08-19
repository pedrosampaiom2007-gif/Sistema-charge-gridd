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
de carga e o gráfico de geração solar prevista) Quando várias estações
estão em uso, o sistema redistribui a energia em tempo real, comunicando
cada limite de potência no padrão aberto OCPP — o mesmo idioma que
carregadores comerciais reais falam. E a tarifa já reage à previsão de
geração solar do dia, dando desconto pro motorista que carrega no horário
de mais sol — o mesmo princípio das operadoras reais do mercado, como a
Driivz."

**Cresceu ~15 palavras em relação à versão anterior** — cronometre esse
bloco especificamente antes de gravar o vídeo final; se passar de 40s, o
primeiro corte aqui é "o mesmo princípio das operadoras reais do mercado,
como a Driivz" (frase que reforça, mas não é essencial).

## 1:15 – 1:50 | Pilar 2 — Sistema de cobrança das recargas (35s)

**FALA:** "O segundo pilar é a cobrança. (MOSTRAR: tela de simulação de
pagamento / tarifação, e o totem pedindo placa + PIN) O ChargeGrid calcula
o valor por energia consumida, com tarifação dinâmica que varia por
horário, ocupação e até previsão de sol — assim como fazem redes reais tipo
Tesla e EVgo. O pagamento passa por um gateway integrado em modo sandbox, e
a conta do motorista é protegida por placa mais PIN de 4 dígitos, com hash
de segurança seguindo boas práticas de LGPD."

## 1:50 – 2:25 | Pilar 3 — Recarga inteligente + interface do usuário (35s)

**FALA:** "O terceiro pilar é a experiência de quem usa. (MOSTRAR: totem,
app do motorista e o chatbot respondendo uma pergunta) Temos três
interfaces conectadas ao mesmo motor: o totem no ponto de recarga, o app do
motorista e um dashboard de gestão pra quem administra a operação. E pra
tirar dúvidas na hora, criamos um chatbot com inteligência artificial que
responde sobre o funcionamento do sistema em tempo real."

*(sem alteração de conteúdo — já era preciso. Atenção só no checklist: a
pergunta que aparecer no vídeo precisa ser uma que o chat responde bem, ver
abaixo.)*

## 2:25 – 2:45 | Diferencial e maturidade do projeto (20s)

**FALA:** "Diferente de um protótipo de papel, o ChargeGrid já está no ar:
banco de dados em nuvem, API funcionando, mais de 50 testes automatizados,
deploy feito e testado. (MOSTRAR: código ou painel de deploy, se der tempo)
Esse é o nosso principal diferencial — não é uma ideia, é um sistema
rodando de ponta a ponta, pronto pra evoluir."

## 2:45 – 3:00 | Próximos passos + fechamento (15s)

**FALA:** "Já temos a tarifa reagindo à previsão de sol e o balanceamento
de carga falando o padrão aberto OCPP — alinhados com o próprio DNA da
GoodWe. Os próximos passos: acesso real à API da GoodWe e um sensor físico
de ocupação de vaga. ChargeGrid Intelligence: gestão de recarga pronta pra
escalar. Obrigado."

**Isso substitui o "queremos conectar à energia solar" da versão anterior**
— não removemos o OCPP e o sensor físico da lista de próximos passos porque
esses dois continuam sendo trabalho futuro de verdade (ver
`docs/TAREFAS_EQUIPE.md`).

---

## Checklist antes de gravar

- [ ] Confirmar que o deploy está online e estável no dia da gravação
      (checar `GET /api/painel` e `GET /api/solar` respondendo, não só a
      tela abrindo — o Render em plano gratuito hiberna e a primeira
      chamada depois de um tempo parado pode falhar uma vez antes de
      responder)
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
