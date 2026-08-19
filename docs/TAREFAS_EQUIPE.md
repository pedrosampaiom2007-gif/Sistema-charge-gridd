# Divisão de tarefas — reta final até 28/ago

Duas frentes, sem dependência forte entre elas: **hardware** (Raul + Luan)
e **software** (Pedro Sampaio + Pedro Ribeiro). Cada tarefa abaixo já vem
com o que precisa pra começar, não é só título solto.

## Hardware — Raul + Luan

A ideia dos dois (um monta/valida no simulador e entrega pronto, o outro
compra e executa em hardware real) é boa e o motivo é simples: shipping de
componente é o gargalo real, não a lógica. Enquanto um valida o
comportamento no Wokwi (grátis, sem esperar entrega de nada), o outro já
pode estar comprando — não precisa esperar a simulação terminar 100% pra
começar a comprar. **Sugestão: decidam a lista de peças juntos nos primeiros
30 minutos e já disparem a compra**, mesmo que a simulação ainda esteja
sendo ajustada. Do jeito que tá descrito (montar → só depois comprar), o
prazo do frete vira gargalo desnecessário.

Um ponto técnico real pra não perder tempo/hardware: o pino ECHO do
HC-SR04 (sensor ultrassônico) sai em 5V, e a maioria dos GPIO do ESP32
tolera só 3,3V — ligar direto pode danificar a placa. Precisa de um divisor
de tensão simples (dois resistores) ou um sensor já 3,3V-compatível. Vale
testar isso no Wokwi antes de ligar em hardware real, já que o simulador
não avisa sobre isso (ele não modela o dano).

### Papel A — Simulação e validação (Wokwi)

1. Montar o circuito no [Wokwi](https://wokwi.com) (ESP32 + sensor
   ultrassônico HC-SR04 pra detectar ocupação de vaga + 1-2 LEDs de status:
   livre/ocupado).
2. Escrever o firmware que lê o sensor e manda o resultado por Wi-Fi (HTTP)
   pra API do ChargeGrid — **o contrato já existe, pronto pra usar**:
   ```
   POST https://chargegrid-api.onrender.com/api/estacoes/<N>/telemetria
   Content-Type: application/json

   { "ocupada": true }
   ```
   `<N>` é o número da estação (1 a 10). Resposta `{"ok": true}` se deu
   certo. Testem primeiro contra `http://127.0.0.1:5000` local antes de
   mandar pro Render.
3. Validar no simulador: LED muda quando "carro" (objeto no Wokwi) se
   aproxima/afasta do sensor, e a chamada HTTP realmente chega na API (dá
   pra conferir vendo o campo `ocupacao_fisica` mudar em
   `GET /api/painel`).
4. Entregar pro Papel B: o código do firmware (arquivo `.ino` ou
   MicroPython) + a lista exata de componentes usados + qualquer ajuste de
   pino que a simulação exigiu.

### Papel B — Compra e montagem física

1. Comprar (pode começar assim que a lista de peças estiver definida, não
   precisa esperar o Papel A terminar 100%): ESP32 (dev board), sensor
   HC-SR04, 2 resistores pro divisor de tensão do ECHO, 1-2 LEDs +
   resistores limitadores, protoboard e jumpers.
2. Montar fisicamente replicando o que foi validado no Wokwi.
3. Carregar o firmware que o Papel A validou (Arduino IDE ou
   equivalente) — não deveria precisar reescrever lógica, só ajustar
   credencial de Wi-Fi real.
4. Testar contra a API de verdade e confirmar que `ocupacao_fisica`
   aparece certo no dashboard.

**Reserva de tempo:** mesmo com a lógica validada em simulação, montagem
física real costuma ter 1-2 rodadas de ajuste (fiação solta, sensor mal
posicionado, Wi-Fi instável) — não tratem essa etapa como "só executar",
separem pelo menos uma sessão extra de debug.

**Se o prazo apertar:** a demonstração em vídeo (28/ago) não depende do
hardware físico — o Wokwi sozinho já mostra o conceito funcionando, e é
exatamente o que a análise de mercado recomendou pra um projeto acadêmico
neste estágio. Terminar o Papel A e deixar o Papel B pra depois da entrega
é uma opção real, não um fracasso.

## Software — Pedro Sampaio + Pedro Ribeiro

> **Nota resolvida:** a mensagem original dizia "Pedro S e \pedro" — o
> segundo nome era Pedro Ribeiro (autocorretor engoliu o resto do nome).
> Ele entrou no lugar de Lucas Garcia no time — README.md e
> `docs/BUSINESS_MODEL.md` já foram atualizados pra refletir isso.

**Pedro Sampaio — execução das melhorias.** Já feito nesta rodada (não é
mais tarefa, é o que já está no repositório):
- Módulo de geração solar simulada (`entregas/solar_optimizer.py`) com
  desconto de tarifa na janela de maior geração prevista.
- DLB comunicando limite de potência no vocabulário OCPP 1.6J
  (`SetChargingProfile`).
- Endpoint `POST /api/estacoes/<n>/telemetria`, pronto pro hardware.
- Correção do roteiro do vídeo (`docs/ROTEIRO_PITCH.md`) e documento de
  posicionamento GoodWe (`docs/GOODWE_ROADMAP.md`).

Próximo, se sobrar tempo:
- **XGBoost como comparação do modelo de demanda**: treinar um XGBoost com
  o mesmo dataset do RandomForest atual (`modelagem_ia/`), comparar
  MAE/RMSE/R² entre os dois, documentar no notebook. Não substitui o
  RandomForest em produção necessariamente — é uma comparação que mostra
  rigor de avaliação de modelo, o tipo de coisa que uma banca de ML valoriza.
- Ligar `ocupacao_fisica` (quando o hardware existir) numa exibição visual
  no dashboard — hoje o campo existe na API mas não aparece em lugar
  nenhum da tela ainda, de propósito (não fazia sentido desenhar UI pra um
  dado que sempre ia estar `null` até o hardware chegar).

**Pedro Ribeiro — ideias e inovações.** Sem código nesta frente — é
pesquisa e direção, não implementação. Sugestão de foco, dado o que já foi
verificado nesta rodada (ver `docs/GOODWE_ROADMAP.md` pras fontes):
- Levantar o que mudaria na história de negócio se o piloto V2G da
  Equatorial Alagoas (aprovado pela ANEEL em fev/2026) virasse um
  paralelo direto pro ChargeGrid — dá pra citar na apresentação como prova
  de que o setor elétrico brasileiro está testando exatamente essa tese.
- Mapear, mesmo sem implementar, como ficaria o modelo de comissão
  (`docs/BUSINESS_MODEL.md` já tem uma proposta 88/12) se a GoodWe entrasse
  como parceira de dado (Open API SEMS) em vez de só fornecedora de
  hardware — muda o valor que a GoodWe ganha da parceria?
- Achados de outras plataformas comerciais (Driivz, AMPECO, ChargePoint)
  que ainda não foram cobertos — qual recurso delas o ChargeGrid poderia
  copiar em uma tarde de trabalho, sem virar overengineering?

## Por que separei assim

Hardware e software não têm dependência forte um do outro até o momento em
que o firmware precisar do endpoint real — que já existe agora, então as
duas frentes podem rodar em paralelo sem se esperar. O único ponto de
sincronização é: se o Papel A/B do hardware terminar, o dado começa a
chegar sozinho no `/api/painel`, sem precisar de deploy novo nem de
ninguém do software mexer em nada.
