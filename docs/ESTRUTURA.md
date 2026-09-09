# Estrutura do repositório

O repositório é dividido em **quatro pastas**, por responsabilidade:

| Pasta | O que tem dentro |
|---|---|
| ⚙️ [`backend/`](../backend/) | Tudo que roda em Python no servidor: o motor (`ev_chargegrid.py`), a API Flask (`api_server.py`), a janela solar (`solar_optimizer.py`), o modelo de IA (`modelo_demanda.pkl` + `modelagem_ia/`), as dependências e os testes do motor. |
| 🖥️ [`frontend/`](../frontend/) | As telas — HTML/CSS/JS puro, sem build: landing page (`index.html`), `totem/` (motorista na estação), `app/` (área pessoal do motorista) e `dashboard/` (painel do gestor). |
| 🤖 [`chatbot/`](../chatbot/) | O assistente conversacional: versão local (`chatbot.py`), versão Colab (`.ipynb`), os guardrails, a base do RAG (`dados_rag.json`) e os testes offline. |
| 📚 [`docs/`](.) | Toda a documentação — instalação, guia de uso, arquitetura, segurança, deploy, changelog, modelo de negócio, roteiro do pitch. |

Na raiz ficam só `README.md`, `render.yaml` (blueprint de deploy) e o `.env` (não versionado).

Estrutura em detalhe, com o que cada arquivo faz: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).

<br>

## De onde veio cada pasta

A partir de 2026-09-09 o código deixou de morar numa pasta única `entregas/`. Se você tem um link, um clone antigo ou um print de tela apontando pro caminho antigo, é este o mapa:

| Antes | Agora |
|---|---|
| `entregas/ev_chargegrid.py` | `backend/ev_chargegrid.py` |
| `entregas/solar_optimizer.py` | `backend/solar_optimizer.py` |
| `entregas/modelo_demanda.pkl` | `backend/modelo_demanda.pkl` |
| `entregas/requirements (1).txt` | `backend/requirements (1).txt` |
| `entregas/files/api_server.py` | `backend/api_server.py` |
| `entregas/files/Procfile` | `backend/Procfile` |
| `entregas/tests/test_ev_chargegrid.py` | `backend/tests/test_ev_chargegrid.py` |
| `modelagem_ia/` | `backend/modelagem_ia/` |
| `entregas/index.html` | `frontend/index.html` |
| `entregas/files/` (totem) | `frontend/totem/` |
| `entregas/app/` | `frontend/app/` |
| `entregas/frontend/` (dashboard) | `frontend/dashboard/` |
| `entregas/chatbot.py` | `chatbot/chatbot.py` |
| `entregas/guardrails.py` | `chatbot/guardrails.py` |
| `entregas/dados_rag.json` | `chatbot/dados_rag.json` |
| `entregas/ChargeGrid_Intelligence_chatbot.ipynb` | `chatbot/ChargeGrid_Intelligence_chatbot.ipynb` |
| `entregas/tests/test_chatbot.py` | `chatbot/tests/test_chatbot.py` |
| `entregas/tests/test_guardrails.py` | `chatbot/tests/test_guardrails.py` |
| `parte_tecnica.txt` | `docs/parte_tecnica.txt` |

Nenhum arquivo foi apagado nem renomeado — só mudaram de pasta. O `.env` continua na **raiz do repositório** (um nível acima de `backend/` e de `chatbot/`), exatamente como antes.
