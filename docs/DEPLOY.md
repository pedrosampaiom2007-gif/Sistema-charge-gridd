# 🚀 Deploy — ChargeGrid Intelligence

Hoje o sistema roda em `localhost` (ver `docs/INSTALL.md`). O repositório já está preparado pra publicar a API num servidor de verdade, sem precisar reescrever nada:

- **`render.yaml`** (raiz do repo): blueprint do [Render](https://render.com) — aponta pra `entregas/files`, instala as dependências e sobe com `gunicorn` (servidor de produção; o servidor embutido do Flask, usado localmente, avisa explicitamente que não deve ser exposto assim).
- **`entregas/files/Procfile`**: mesma ideia, pra Railway ou qualquer host compatível com Procfile.
- Em ambos, configure `DATABASE_URL`, `GROQ_API_KEY` e `FLASK_DEBUG=0` como variáveis de ambiente no painel do serviço — nunca no código. `FLASK_DEBUG=0` é obrigatório num servidor público: com debug ligado, o Werkzeug expõe um console interativo que permite executar código remotamente.
- Opcionais: `SOLAR_LATITUDE`/`SOLAR_LONGITUDE` (padrão: São Paulo) ajustam onde a previsão de geração solar é calculada; `TELEMETRIA_TOKEN` protege `POST /api/estacoes/<n>/telemetria` — configure antes de conectar hardware de verdade numa API pública (ver `docs/SECURITY.md`).
- Depois da API publicada, troque `API_BASE` no topo de cada `app.js` (totem, dashboard, app) pra a URL pública, e sirva os HTMLs estáticos em qualquer host (GitHub Pages, Vercel, Netlify — são arquivos estáticos, não precisam de servidor Python).

Nenhuma conta é criada nem publicada automaticamente por esses arquivos — eles só deixam o repositório pronto pra quando alguém do time conectar uma conta existente (Render/Railway) e publicar.
