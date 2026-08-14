# Modelo de Negócio — ChargeGrid Intelligence

## Visão geral

O **ChargeGrid Intelligence** é uma plataforma comercial de gestão de eletropostos, feita pra operadores que têm múltiplos pontos de carga de alto fluxo — shopping centers, estacionamentos comerciais, redes de varejo — e precisam de algo além de "o carregador liga e desliga": tarifação que reage à demanda real, um histórico de pagamento que o cliente confia, e um assistente que responde perguntas de negócio sem expor o que é confidencial.

A plataforma cobre o ciclo inteiro sozinha: autoatendimento no totem, cobrança simulada (Pix/cartão/app), painel operacional pro gestor, área pessoal do motorista com suporte a mais de um carro por conta, e um assistente conversacional — tudo rodando em cima de um banco na nuvem (Postgres/Supabase), publicado e acessível de qualquer lugar, não só de uma máquina específica.

## O problema

Recarga comercial de veículo elétrico não é só "vender kWh". Um operador de estacionamento com 10 pontos de carga precisa, ao mesmo tempo:

- saber, em tempo real, quais pontos estão livres e quanto de potência da rede está sendo usada (sem estourar o limite contratado);
- cobrar de um jeito que reflita o custo real de operar no horário de pico, sem simplesmente "aumentar o preço sempre";
- dar ao motorista um jeito de conferir o que já pagou sem que qualquer pessoa que souber a placa consiga ver o histórico de outra;
- tirar um carregador de circulação temporariamente (manutenção, cabo danificado) sem derrubar o sistema nem perder esse estado a cada reinício;
- e, cada vez mais, oferecer suporte automatizado — sem que isso vire um jeito indireto de vazar faturamento pra qualquer pessoa que converse com o chat.

A maioria das soluções desse porte resolve pedaços disso isoladamente (um app de pagamento, uma planilha de controle, um totem sem inteligência nenhuma). O ChargeGrid junta as peças numa coisa só, com a persistência e a segurança tratadas como requisito desde o início, não como reforço depois de um incidente.

## Nossa solução

- **Dashboard em tempo real**, com login de administrador de verdade (não senha fixa sem controle) — faturamento, curva de demanda prevista por IA, e estado de cada estação.
- **Tarifação dinâmica** por horário, ocupação simultânea e demanda prevista por um modelo de machine learning (RandomForest treinado com dados reais) — inclusive desconto de madrugada, pra incentivar o motorista a carregar fora do pico em vez de só cobrar mais caro dentro dele.
- **Balanceamento de carga (DLB)** entre as estações ativas, respeitando o limite de potência da rede.
- **Contas com PIN**, suportando mais de uma placa por pessoa — histórico de pagamento protegido por autenticação de verdade.
- **Manutenção de estação**: um carregador com defeito sai de circulação sem sumir do sistema, e sem interromper quem já está no meio de uma sessão.
- **Assistente com IA de verdade** (LLM via Groq), que responde tanto sobre o sistema quanto dúvidas gerais de carro elétrico — com uma fronteira de acesso que impede o motorista de puxar faturamento do negócio pelo chat, e libera esse mesmo dado pra quem está logado como gestor.
- **Relatório do dia** exportável em um clique, pro gestor levar o resumo da operação pra fora do sistema.
- **Banco na nuvem**: qualquer terminal — totem, dashboard, app do motorista — lê e escreve no mesmo estado, de qualquer lugar, não só de uma máquina que precisa ficar ligada no local.

## Público-alvo

Estabelecimentos comerciais que quiserem oferecer recarga como diferencial competitivo e fonte de receita adicional, com múltiplos pontos de carga e fluxo alto o suficiente pra justificar gestão ativa (não só "um carregador na vaga de visitante"):

- Shopping centers e centros comerciais
- Estacionamentos comerciais
- Redes de varejo com estacionamento próprio
- Empresas com frota ou estacionamento para clientes/funcionários

## Stakeholders

**GoodWe** — fornece a base tecnológica de referência do desafio (hardware de carregador) e é remunerada por uma comissão sobre cada sessão de recarga paga na plataforma.

**Estabelecimento comercial** — adquire e opera o ChargeGrid Intelligence, disponibiliza os pontos de carga aos clientes, e fica com a maior parte da receita de cada sessão.

**Administrador** — opera o dia a dia: dashboard, relatório, manutenção de estação, e o assistente em modo de gestão.

**Motorista** — usuário final: recarrega no totem, acompanha o histórico e conversa com o assistente pelo app, sem depender do administrador pra nada disso.

## Fluxo operacional

O fluxo é automatizado ponta a ponta:

```
Motorista chega ao totem
        │
Digita a placa (ou se cadastra na hora, se for a primeira vez)
        │
Totem valida contra o banco e inicia a sessão — sem intervenção do operador
        │
Tarifa é calculada dinamicamente (horário + ocupação + demanda prevista pela IA)
        │
Motorista encerra no totem → cobrança simulada (Pix) → recibo
        │
Pagamento confirmado automaticamente
        │
        ├── 88% → Estabelecimento Comercial   (modelo proposto — split
        └── 12% → GoodWe (comissão)            ainda não calculado pelo sistema, ver "Modelo comercial")
```

O administrador só entra no fluxo pra decisões operacionais: marcar manutenção, consultar relatório.

## Modelo comercial

Comissão por uso: **12% de cada sessão paga** fica com a GoodWe como remuneração pela plataforma (software de gestão) e pelo hardware de referência; os outros **88%** ficam com o estabelecimento comercial, que é quem assume o investimento em infraestrutura e atendimento ao público.

O percentual não foi escolhido no escuro — está na faixa praticada em modelos comparáveis:

- **Marketplaces e plataformas de intermediação** (apps de delivery, reserva de serviços) costumam cobrar entre 10% e 25% por transação.
- **Royalties de franquia** no Brasil giram tipicamente entre 5% e 12% do faturamento.
- **Gateways de pagamento puros** (Pix, cartão) cobram separadamente, entre 1% e 4% — não estão incluídos nesse percentual, porque remuneram só o processamento do pagamento, não o software de gestão nem o hardware.

12% fica no teto inferior dessa faixa de propósito: mantém a plataforma competitiva e favorece a adoção inicial por parte do estabelecimento, que é quem carrega o investimento fixo (instalação, energia, espaço). O percentual é uma decisão comercial, não uma trava técnica — pode ser renegociado por volume de sessões ou tipo de contrato. **Isso ainda não é uma funcionalidade implementada no sistema**: hoje o motor registra o valor total de cada sessão (`valor_sessao`), não o repasse entre estabelecimento e GoodWe — calcular e registrar o split faria parte de uma próxima etapa, não do MVP atual.

## Formas de pagamento

Já implementado, não é promessa futura: o gateway simulado (sandbox Mercado Pago) cobre Pix, cartão, app e QR code — a arquitetura já isola o gateway de pagamento (`criar_pagamento_sandbox`) do resto do motor, então trocar o sandbox por uma integração real não exige tocar em sessão, tarifação ou histórico.

## Papel da Inteligência Artificial

A IA aqui não é um recurso decorativo — ela participa de duas decisões de negócio de verdade:

- **Previsão de demanda** (RandomForest treinado com dados reais de sessões), usada tanto no gráfico do dashboard quanto na própria tarifação: horas de demanda prevista alta custam mais, horas de baixa demanda (madrugada) custam menos.
- **Assistente conversacional** (LLM via Groq, com busca por relevância num histórico real de sessões), que combina dado em tempo real do banco com contexto histórico — e aplica controle de acesso: o que o motorista pergunta nunca revela faturamento ou receita agregada do negócio, e o que o administrador pergunta tem acesso completo. Essa fronteira existe porque um chat sem ela vira um jeito indireto de vazar dado de negócio pra qualquer cliente que souber perguntar.

## Diferenciais da solução

- Nuvem desde o início, acessível de qualquer lugar, não só de uma máquina específica.
- Tarifação dinâmica de verdade (horário + ocupação + IA), com incentivo de madrugada, não só sobretaxa de pico.
- Autenticação real em cada camada (PIN do motorista, login do admin).
- Assistente com IA de linguagem natural real, com fronteira de dado de negócio.
- Manutenção de estação como estado de primeira classe: persistido no banco, com regras próprias de bloqueio.
- Já publicado e acessível publicamente, pronto pra demonstração fora do ambiente de desenvolvimento.

## Visão de produto

O ChargeGrid Intelligence é pensado como uma plataforma SaaS de gestão de recarga comercial: quem contrata não compra um totem, compra a operação inteira — tarifação inteligente, controle de acesso, suporte automatizado e visibilidade operacional — com a GoodWe remunerada pelo uso da plataforma, não pela venda de um produto fechado.

## Equipe

Pedro Sampaio, Raul Sampaio, Lucas Garcia, Luan de Araujo, Kevin Rodrigues, Pedro Ribeiro Lopes — EV Challenge 2026, GoodWe / FIAP.
