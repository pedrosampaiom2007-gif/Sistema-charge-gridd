# ChargeGrid Intelligence (CGI) — Core Engine
> **Plataforma de Gestão Comercial de Recarga para Veículos Elétricos (EV)**
> *GoodWe Challenge — FIAP (Sprint 2 & 3)*

Este repositório contém o **motor principal (Core Backend)** do sistema ChargeGrid Intelligence. Desenvolvido em Python, este script centraliza todas as regras de negócio comerciais, simula o comportamento de um ecossistema de postos públicos/privados de alto fluxo (shoppings, aeroportos e frotas) e serve como a fundação arquitetural para as próximas evoluções do projeto.

---

##  Contexto do Projeto (Escopo Comercial)
Diferente de soluções residenciais ou condominiais (focadas em apenas um veículo e sem rateio complexo), o ChargeGrid Intelligence foi projetado para ambientes **comerciais de alto fluxo**, suportando:
* **Múltiplos usuários independentes** por sessão simultaneamente.
* **Autenticação segura** por placa ou ID de usuário via aplicativo.
* **Faturamento individualizado** (Billing) por sessão de recarga.
* **Tarifação dinâmica** inteligente baseada em horário, demanda local e congestionamento.
* **Dynamic Load Balancing (DLB)** automatizado para proteção da infraestrutura elétrica.
* **Protocolo OCPP 1.6J** integrado via simulação de mensagens JSON com o Central System.

---

## 🚀 Como o Sistema Funciona Hoje

O script atual simula um cenário real com um limite de demanda contratada (`50.0 kW`) compartilhado por até `10 estações` de recarga simultâneas. O sistema opera baseado em 4 pilares técnicos principais:

1.  **Gestão de Sessões Comerciais (`SessaoRecarga`):** Cada sessão é isolada, possui identificação única do usuário (placa ou ID do app), registra consumo acumulado (kWh) e exige um método de pagamento para faturamento individual.
2.  **DLB (Dynamic Load Balancing) Automático:** A função `balancear_carga()` monitora as estações ativas e redistribui a potência disponível de forma igualitária, garantindo que a demanda contratada com a concessionária de energia nunca seja ultrapassada, evitando multas e quedas de energia.
3.  **OCPP 1.6J Simulador:** Todas as ações críticas (início de recarga, envio de telemetria e encerramento) geram payloads estruturados no padrão JSON seguindo o protocolo oficial de recarga de EVs (`StartTransaction`, `MeterValues`, `StopTransaction`).
4.  **Tarifação Dinâmica por IA Inteligente:** O preço do kWh flutua dinamicamente com base em três camadas sobrepostas na função `ia_calcular_tarifa()`:
    * Horário de pico comercial (Almoço às 12h e saída do trabalho entre 18h e 20h).
    * Congestionamento local (Ocupação de 3 ou mais estações simultâneas).
    * Fator preditivo de demanda histórica (Simulando uma IA que já conhece os hábitos de consumo do local).

---

##  Instruções de Execução

Para rodar o simulador interativo e validar o comportamento do sistema no terminal:

1.  Certifique-se de ter o Python 3.10 ou superior instalado na sua máquina.
2.  Baixe o arquivo principal do código (`ev_chargegrid.py`).
3.  Abra o terminal na pasta do arquivo e execute o comando:
    ```bash
    python ev_chargegrid.py
    ```
4.  O sistema iniciará rodando automaticamente uma **Demonstração Comercial**, provando o funcionamento em tempo real do DLB e da Tarifação dinâmica em 4 cenários comuns de um shopping center.
5.  Após o término da demo, utilize o **Menu Interativo** no terminal para simular novas entradas de clientes, passagens de tempo de recarga (+30 min) e encerramento com emissão de recibos comerciais.

---

##  Roadmap de Evolução Arquitetural (Alterações Futuras)

** IMPORTANTE PARA O TIME:** À medida que o projeto avançar e o quadro do Trello evoluir, este código estático servirá de base e sofrerá alterações modulares. Abaixo estão mapeados os pontos exatos onde cada membro deverá injetar suas implementações:

### 1. Persistência e Banco de Dados
* **Responsável:** M2 (Backend)
* **Onde mudar no código:** A lista em memória `estacoes: list[SessaoRecarga]` deve ser descontinuada.
* **Alteração futura:** As funções `iniciar_sessao()`, `simular_tempo()` e `encerrar_sessao()` deverão realizar queries estruturadas de `INSERT` e `UPDATE` diretamente em um banco de dados relacional ou NoSQL para manter o histórico de consumo seguro e persistente.

### 2. Integração com Gateway de Pagamento Real
* **Responsável:** M2 (Backend)
* **Onde mudar no código:** A função `encerrar_sessao()`.
* **Alteração futura:** Em vez de apenas imprimir o valor textual do recibo em tela, a função deverá disparar uma requisição de API para um ambiente de testes externo (Stripe ou Mercado Pago Sandbox) para validar a cobrança real do usuário antes de liberar a vaga do posto.

### 3. Substituição por IA Preditiva de Machine Learning
* **Responsável:** M5 (Cientista de Dados)
* **Onde mudar no código:** A função `ia_prever_demanda()` e o dicionário estático `DEMANDA_PREVISTA_POR_HORA`.
* **Alteração futura:** Remover o dicionário fixo e carregar um modelo preditivo real gerado via `scikit-learn` (treinado com a base de dados histórica de 60 sessões da SP2). O script passará a ler um arquivo serializado `.pkl` ou `.onnx` para prever os picos de demanda com precisão estatística.

### 4. Conexão com Chatbot RAG
* **Responsável:** M3 (Engenheiro de IA)
* **Onde mudar no código:** Criação de rotas de leitura ou exportação de logs automatizada.
* **Alteração futura:** O pipeline construído em LangChain consumirá os dados de logs e relatórios gerados por este simulador para que o assistente virtual (Llama 3.2) consiga responder perguntas de negócio em tempo real para os gestores (ex: *"Qual o faturamento acumulado agora no posto?"*).

### 5. Consumo de Dados pelo Dashboard Web
* **Responsável:** M4 (Designer UI / Frontend)
* **Onde mudar no código:** Saída de dados da função `painel_operacional()`.
* **Alteração futura:** A função deixará de exibir informações apenas textuais no terminal e passará a enviar os dados de potência ativa do DLB e receita acumulada via API REST ou WebSockets para alimentar graficamente os dashboards visuais desenvolvidos no front-end.

---
*Nota: Este documento deve ser atualizado pelo Product Owner (PO) do grupo sempre que uma nova integração de módulo for concluída com sucesso.*
