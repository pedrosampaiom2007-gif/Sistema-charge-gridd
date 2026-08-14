# 📖 Guia de Uso — ChargeGrid Intelligence

Este guia explica como usar o ChargeGrid Intelligence no dia a dia, sem entrar em detalhes técnicos de código. Se você procura como instalar e rodar o projeto, veja [`docs/INSTALL.md`](INSTALL.md).

O sistema tem **três telas**, cada uma pensada pra um tipo de pessoa diferente: o **totem** (motorista, na estação), o **app** (motorista, no celular/computador, fora da estação) e o **dashboard** (administrador). Todas começam pela página inicial (`entregas/index.html`), que pergunta quem você é.

<br>

## 🔌 Totem — recarregando o veículo

Tela pensada pra ser rápida, sem login: o motorista chega, digita a placa, e sai carregando.

### Iniciar uma recarga

1. Na tela inicial do totem ("Estação disponível"), toque em **Iniciar recarga**
2. Digite a **placa** do veículo
3. Escolha a **forma de pagamento**: Pix, Cartão, App ou QR Code
4. Toque em **Confirmar e carregar**

> **Primeira vez usando essa placa?** Se ela não estiver cadastrada, o totem pede seu nome ali mesmo e já cadastra na hora — não precisa ir ao app antes.

### Durante a recarga

A tela mostra em tempo real: energia consumida (kWh), valor acumulado e tempo decorrido.

### Encerrar e pagar

1. Toque em **Encerrar e pagar**
2. Escaneie o **QR Code Pix** que aparece na tela com o app do seu banco
3. Depois da confirmação, aparece o **recibo** na tela — pronto

### Se a estação estiver em manutenção

Quando um administrador marca aquela estação como indisponível, o totem mostra "Estação em manutenção" direto na tela inicial, sem deixar nem começar o fluxo de recarga — evita frustração de preencher tudo pra descobrir só no final que não dá.

<br>

## 📱 App do motorista — "Minha Conta"

Pra usar fora da estação: conferir gastos, adicionar mais de um carro à mesma conta, ou tirar dúvidas com o assistente.

### Entrar

1. Abra a tela "Minha Conta"
2. Digite a **placa** e o **PIN de 4 números** que você cadastrou (no totem, ou no cadastro do próprio app)
3. Toque em **Entrar**

> **Esqueceu se já tem cadastro?** O link **"Ainda não tem cadastro? Cadastre-se"**, embaixo do formulário de login, leva direto pro cadastro.

### Ver histórico de pagamentos

Depois de logado, a seção **"Meus pagamentos"** mostra todas as sessões de recarga feitas com aquela conta — de qualquer uma das placas vinculadas, não só a que você usou pra logar.

### Adicionar outro carro à mesma conta

1. Toque em **+ Adicionar carro**
2. Digite a placa do novo veículo
3. Pronto — a partir de agora, o histórico dos dois carros aparece junto, e você pode logar com qualquer uma das duas placas (mesmo PIN)

### Conversar com o assistente

Na seção **"Assistente ChargeGrid"**, digite sua pergunta em texto livre. Dá pra perguntar sobre:
- Seus próprios gastos ("quanto eu gastei esse mês?")
- Disponibilidade de estação ("tem carregador livre agora?")
- Dúvidas gerais sobre carro elétrico ("qual a diferença entre carga rápida e lenta?")

O assistente **nunca mostra dado de faturamento do negócio** nessa tela — só o que é seu.

<br>

## 🖥️ Dashboard — painel do administrador

Visão operacional completa da estação, só acessível com login.

### Entrar

1. Na tela do dashboard, preencha **usuário** e **senha** de administrador
2. Toque em **Entrar**

*(Se você é da equipe testando localmente e não sabe o usuário/senha, veja `docs/INSTALL.md`.)*

### Visão geral

Logo no topo, 4 indicadores atualizados em tempo real:
- **Faturamento** do dia
- **Sessões** realizadas
- Estações **ativas** (de 10)
- **Consumo** total (kWh)

Mais abaixo, o **grid de estações** mostra o status de cada uma das 10 (Livre / Ocupada / Manutenção) e um gráfico com a **curva de demanda prevista pela IA** nas próximas 24h.

### Colocar uma estação em manutenção

1. Numa estação com status **Livre**, clique em **Colocar em manutenção**
2. Opcionalmente, escreva o motivo (ex.: "cabo danificado")
3. Confirme

A estação passa a aparecer como indisponível também no totem, e ninguém consegue iniciar sessão nela até você liberar de novo.

> Não dá pra colocar em manutenção uma estação que está **ocupada** no momento — precisa esperar a sessão em andamento terminar primeiro.

### Baixar o relatório do dia

Clique no botão de relatório no topo da lista de estações — baixa um `.txt` com faturamento, número de sessões, ticket médio e consumo do dia, pronto pra levar pra fora do sistema (numa reunião, por exemplo).

### Sair

Botão **Sair**, no canto superior. Diferente de só fechar a aba, isso invalida o seu login de verdade do lado do servidor — ninguém mais consegue usar aquele mesmo acesso depois.

<br>

## 🤖 Sobre o assistente (resumo rápido)

O mesmo assistente aparece tanto no app do motorista quanto (em modo mais completo) pro administrador logado. A diferença é o que cada um pode ver:

| Quem pergunta | O que o assistente pode responder |
|---|---|
| Motorista (logado) | Próprios gastos, disponibilidade de estação, dúvidas gerais |
| Ninguém logado | Só disponibilidade de estação e dúvidas gerais |
| Administrador (logado) | Tudo o que o motorista vê, mais faturamento e dados agregados do negócio |

Essa separação existe de propósito: mesmo que alguém descubra a URL do assistente sem passar pelo app ou pelo dashboard, não consegue puxar dado sensível do negócio por ali.
