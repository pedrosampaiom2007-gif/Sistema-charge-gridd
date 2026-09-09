# frontend/

As telas do sistema — HTML, CSS e JavaScript puro, sem build e sem dependência de instalar nada. É só abrir `index.html` no navegador (ou servir a pasta como arquivos estáticos).

| Pasta | Pra quem | O que faz |
|---|---|---|
| `index.html` | todo mundo | Landing page — pergunta se você é motorista ou administrador. |
| `totem/` | motorista, na estação | Self-service: digita a placa, carrega, encerra, paga por QR Pix e vê o recibo. Cada totem serve uma estação — escolha qual com `totem/index.html?estacao=3`. |
| `app/` | motorista, no celular | Área pessoal: login por placa + PIN, histórico de pagamentos, mais de um carro por conta e o chat com o assistente. |
| `dashboard/` | gestor | Painel operacional: as 10 estações ao vivo, KPIs do dia, medidor da rede e os gráficos de demanda e geração solar. Requer login de admin. |

As três telas falam com a API Flask de [`backend/`](../backend/) por `fetch`. Se a API não estiver rodando em `http://localhost:5000`, ajuste a constante `API_BASE` no topo de cada `app.js`.

Guia de uso de cada tela, com o passo a passo: [`docs/USER_GUIDE.md`](../docs/USER_GUIDE.md).
