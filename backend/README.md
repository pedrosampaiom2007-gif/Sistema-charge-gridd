# backend/

Tudo que roda em Python no servidor.

| Arquivo | O que é |
|---|---|
| `ev_chargegrid.py` | Motor do sistema — banco (Postgres/Supabase), autenticação por placa, contas, pagamento, balanceamento de carga (DLB) e tarifação com IA preditiva. É a única fonte de verdade: API, telas e chatbot leem dele. |
| `api_server.py` | Camada Flask que expõe o motor via HTTP/JSON pras 3 telas e pro chatbot. |
| `solar_optimizer.py` | Previsão de geração solar (Open-Meteo) e a janela de desconto solar aplicada na tarifa. |
| `modelo_demanda.pkl` | Modelo RandomForest treinado (previsão de demanda por hora). |
| `requirements (1).txt` | Dependências Python. O nome tem espaço e parêntese mesmo — use aspas ao instalar. |
| `Procfile` | Comando de start pra deploy (Render/Railway). |
| `modelagem_ia/` | Como o `modelo_demanda.pkl` foi treinado — histórico, não roda em produção. |
| `tests/` | Testes do motor, com o banco mockado (não escrevem no Postgres de verdade). |

## Como rodar

Com o `.env` já criado na raiz do repositório (`DATABASE_URL` e `GROQ_API_KEY` — ver [`docs/INSTALL.md`](../docs/INSTALL.md)):

```powershell
cd backend
pip install -r "requirements (1).txt"
python api_server.py
```

A API sobe em `http://localhost:5000`. As telas ficam em [`frontend/`](../frontend/) — abra `frontend/index.html` no navegador.

## Testes

Da raiz do repositório:

```powershell
python -m unittest discover -s backend/tests -v
```
