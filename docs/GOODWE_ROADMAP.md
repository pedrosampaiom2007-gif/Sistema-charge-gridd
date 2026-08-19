# Roadmap de integração com o ecossistema GoodWe

Este documento separa duas coisas que é fácil confundir numa apresentação: o
que o ChargeGrid Intelligence **já fala a mesma língua** que o ecossistema
GoodWe, e o que seria **preciso negociar/instalar** pra virar uma integração
de verdade. Escrito depois de checar as duas afirmações externas mais
importantes (API da GoodWe e o piloto regulatório de V2G), pra não repetir
número solto sem fonte num pitch.

## O que já está no sistema hoje

- **Janela de desconto solar** (`entregas/solar_optimizer.py`): o motor busca
  a previsão de radiação solar do dia (Open-Meteo, API pública sem chave) e
  aplica um desconto de até 10% na tarifa nas horas de maior geração
  prevista — desde que não seja horário de pico. É a mesma ideia de "tarifa
  inteligente que reage à disponibilidade solar" que a GoodWe já promove com
  o app SEMS, só que hoje reagindo a uma **previsão pública de tempo**, não a
  uma **leitura real de inversor**.
- **DLB falando o vocabulário OCPP 1.6J** (`ev_chargegrid.balancear_carga`):
  o balanceamento de carga entre estações continua sendo rateio igualitário
  — não mudamos o algoritmo de decisão — mas agora ele comunica o limite de
  potência de cada estação através de uma mensagem `SetChargingProfile`, no
  formato real do protocolo (`chargingProfileId`, `stackLevel`,
  `chargingProfilePurpose`, `chargingRateUnit`, `limit`), o mesmo padrão que
  carregadores comerciais reais (inclusive a linha HCA da GoodWe) usam pra
  aceitar limite de potência de um sistema de gestão.
- **Tarifação dinâmica completa**: horário de pico, ocupação simultânea,
  demanda prevista por IA, desconto de madrugada e agora desconto solar —
  cinco sinais diferentes, todos compondo o mesmo preço final.

## O que uma integração real mudaria

| Hoje (simulado) | Com acesso GoodWe real |
|---|---|
| Previsão de sol via Open-Meteo (meteorologia pública) | Geração **medida** direto do inversor, via Open API SEMS |
| Totem = página web, sem hardware | Carregador GoodWe HCA falando OCPP de verdade com a API |
| Sem bateria/armazenamento no modelo | SEMS já gerencia bateria — o excedente solar não usado na recarga poderia ser armazenado, não perdido |
| DLB fala a linguagem OCPP, mas decide sozinho | Perfil de carga poderia vir do próprio SEMS, coordenado com o resto da instalação (não só o carregador) |

## Por que isso não está implementado agora (e por que não fingir que está)

A [Open API SEMS da GoodWe](https://openapi.goodwe.com/) existe de verdade,
mas é liberada **só pra conta de organização**, mediante contato com o time
de vendas da GoodWe e assinatura de um NDA — não é uma chave que se gera
sozinho num cadastro. Sem uma instalação GoodWe real conectada à nossa
conta, não tem como consumir dado de inversor de verdade; a previsão pública
de tempo é o substituto honesto disponível pra um projeto acadêmico, e é
isso que está rodando hoje.

## Por que isso importa pro cenário regulatório brasileiro

Em fevereiro de 2026, a ANEEL aprovou o primeiro piloto regulatório de V2G
do país, conduzido pela Equatorial Alagoas — 22 meses de execução (início em
fevereiro de 2026, fim previsto pra novembro de 2027), testando justamente
**tarifas inteligentes que incentivam horário de recarga mais eficiente e
melhor uso da energia solar e de baterias**. É a mesma tese do ChargeGrid,
validada como digna de um piloto regulatório formal — não é só uma ideia de
grupo de desafio, é o que o setor elétrico brasileiro está testando agora.

## Próximos passos concretos (não implementados ainda)

Acesso à Open API SEMS da GoodWe **já foi perguntado e negado** pelos
organizadores do desafio — não é mais um próximo passo em aberto, é um
limite conhecido do que dá pra fazer nesta rodada. O roadmap abaixo não
depende disso:

1. Trocar a mensagem `SetChargingProfile` simulada por uma implementação
   real de cliente OCPP 1.6J (WebSocket), testável contra um carregador
   simulado (`charger-simulator`/OpenOCPP) antes de qualquer hardware físico.
2. Sensor físico de ocupação de vaga (ver `docs/TAREFAS_EQUIPE.md`) alimentando
   o mesmo `/api/painel` que já existe — a API não precisaria mudar de forma,
   só ganhar uma fonte de dado adicional.

## Fontes

- [GoodWe OpenAPI Developer Platform](https://openapi.goodwe.com/) e o processo de acesso via NDA/conta de organização — [guia de configuração (Solytic)](https://solytic.com/knowledge/set-up-api-access-goodwe-sems-api/).
- Piloto V2G da Equatorial Alagoas aprovado pela ANEEL em fevereiro de 2026 — [SMABC](https://smabc.org.br/alagoas-tera-primeiro-projeto-de-v2g-do-pais-com-aval-da-aneel/), [Canal VE](https://canalve.com.br/alagoas-tera-primeiro-projeto-v2g-pais-aval-aneel/).
