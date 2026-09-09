# chatbot/

O assistente conversacional do ChargeGrid. Responde tanto sobre o sistema (dado real, lido do mesmo motor que a API usa) quanto dúvidas gerais de carro elétrico.

| Arquivo | O que é |
|---|---|
| `chatbot.py` | Versão local, roda num terminal. É esta que a API importa pra servir a rota `/api/chat`. |
| `ChargeGrid_Intelligence_chatbot.ipynb` | Mesma lógica em notebook, pra rodar no Google Colab sem instalar nada. Baixa os arquivos direto do GitHub. |
| `guardrails.py` | Filtro contra prompt injection e uso indevido — roda antes de qualquer coisa chegar no modelo. |
| `dados_rag.json` | Histórico de 60 sessões reais, base da busca do RAG. |
| `tests/` | Testes offline (não precisam de chave da Groq nem do banco). |

A IA roda na nuvem (Groq), não localmente — nada de baixar modelo. O motor vem de [`backend/`](../backend/) e as credenciais (`DATABASE_URL`, `GROQ_API_KEY`) do `.env` na raiz do repositório.

## Como rodar

```powershell
cd chatbot
python chatbot.py
```

Não precisa da API estar no ar — o chatbot fala direto com o Postgres.

## Testes

Da raiz do repositório:

```powershell
python -m unittest discover -s chatbot/tests -v
```
