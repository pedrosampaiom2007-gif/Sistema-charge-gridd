# ChargeGrid Intelligence — Responsabilidades do Projeto
> EV Challenge 2026 — GoodWe / FIAP · Atualizado por Pedro Sampaio · Entrega final: meados de agosto/2026

> ⚠️ **O que falta de verdade, resumido:** só o `dashboard.py` + protótipos do Luan (14/07) e a integração final do Pedro (25/07). Todo o resto já está pronto e integrado.

> 🔓 **Alterações e ideias:** qualquer integrante pode alterar, melhorar ou propor algo em qualquer arquivo já entregue. **Basta avisar o Pedro antes ou logo depois da alteração**, para manter este README e o Kanban coerentes com o que está rodando de verdade.

## Equipe

| Etiqueta | Integrante | Função |
|---|---|---|
| ⚪ | Pedro Sampaio | Líder, integrador final |
| 🔵 | Raul Sampaio | Backend — banco, auth, pagamento |
| 🟡 | Lucas Garcia | IA/Chatbot — RAG + LLM local |
| 🔴 | Luan de Araujo | Frontend — dashboard, protótipos |
| 🟢 | Kevin Rodrigues | Dados/ML — análise + IA preditiva |

## Status Consolidado

| Módulo | Responsável | Status |
|---|---|---|
| `ev_chargegrid.py` (motor, SQLite, auth SHA-256, LGPD, Mercado Pago sandbox, 4 funções de leitura) | Raul | ✅ Concluído |
| `dados_rag.json` (60 sessões reais processadas: receita, pico, DLB, 21 frases RAG) | Kevin | ✅ Concluído |
| `modelo_demanda.pkl` + notebook de treino + gráfico comparativo (RandomForest) | Kevin/Pedro | ✅ Concluído |
| Integração do modelo no motor (`ia_prever_demanda`) | Pedro | ✅ Concluído |
| `ChargeGrid_Intelligence_chatbot.ipynb` (roteador tempo real + RAG + LLM local Ollama, 9 testes, `resultados_testes_sprint3.json`) | Lucas | ✅ Concluído |
| `requirements.txt` | Kevin | ✅ Concluído |
| **`dashboard.py` (Streamlit) + protótipos Totem/App/QR Pix** | **Luan** | 🔴 **FALTA — prazo 14/07** |
| **Integração final ponta a ponta** | **Pedro** | 🔴 **FALTA — prazo 25/07** |
| **Vídeo, slides, submissão** | **Pedro** | 🔴 **FALTA — meados de agosto** |

## Arquitetura Final

```
ev_chargegrid.py (motor)
├── SQLite (chargegrid.db) — tabelas usuarios + sessoes ✅
├── Auth SHA-256 + máscara LGPD ✅
├── Mercado Pago Sandbox (USAR_API_REAL_MERCADOPAGO=False) ✅
├── ia_prever_demanda() → modelo_demanda.pkl (RandomForest, dados reais SP2) ✅
└── 4 funções de leitura (API interna p/ Lucas e Luan) ✅

ChargeGrid_Intelligence_chatbot.ipynb (Lucas)
├── Ollama local (llama3.2:3b) — LLM sem custo, sem API paga ✅
├── Roteador por palavra-chave: tempo real (banco) vs. histórico (RAG) ✅
├── dados_rag.json (Kevin) — substitui os 12 documentos inventados do Sprint 2 ✅
└── 9 casos de teste → resultados_testes_sprint3.json ✅

dashboard.py + protótipos (Luan) — 🔄 em andamento, prazo 14/07
```

## Por que cada peça importa

- **`ev_chargegrid.py`**: é a fonte única de verdade em tempo real. Tudo (chatbot, dashboard, IA) lê dele — sem ele nada mais funciona.
- **`dados_rag.json`**: sem ele o chatbot responderia com dados inventados para sempre, mesmo com o sistema rodando de forma diferente.
- **`modelo_demanda.pkl`**: troca "chute" por previsão baseada nas 60 sessões reais — prova de que a IA preditiva é real, não decorativa.
- **`ChargeGrid_Intelligence_chatbot.ipynb`**: entrega o diferencial de custo zero (LLM local via Ollama) e mostra o sistema respondendo com dados reais e atuais ao mesmo tempo.
- **`requirements.txt`**: garante que qualquer pessoa (incluindo a banca) consiga rodar o projeto sem erro de dependência.
- **`dashboard.py` + protótipos (Luan)**: é a última peça visual — sem ela a demonstração fica só em terminal/notebook.

## Dependências Críticas

```
Raul (banco + 4 funções) ✅
  ├── Lucas usa no chatbot ✅
  └── Luan vai usar no dashboard (pendente)

Kevin (dados_rag.json + modelo_demanda.pkl) ✅
  └── Lucas usa no RAG ✅

Luan (dashboard + protótipos) → Pedro (integração final 25/07) → vídeo/slides (agosto)
```

## Checklist da Integração Final (25/07)
Demo grava no banco → dashboard mostra dados reais → chatbot responde com números reais → protótipos navegam sem erro → QR Code aparece no encerramento.



## Estrutura de Pastas (Repositório)

```
/entregas/
  ev_chargegrid.py, chargegrid.db, dados_rag.json,
  modelo_demanda.pkl, requirements.txt,
  ChargeGrid_Intelligence_chatbot.ipynb
  /modelagem_ia/
    Treinamento_Modelo_Demanda_Sprint3.ipynb
    grafico_comparativo.png
  /dashboard/          ← Luan entrega aqui
```

*Atualizar a cada mudança real de status (não a cada prazo planejado). Qualquer alteração em arquivo já entregue deve ser avisada ao Pedro.*
