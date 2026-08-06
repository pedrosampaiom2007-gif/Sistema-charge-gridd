# modelagem_ia/

Processo de treino do modelo de previsão de demanda usado pelo sistema (`ia_prever_demanda` em `entregas/ev_chargegrid.py`). Não precisa rodar nada aqui pra usar o sistema — é só o histórico/documentação de como `entregas/modelo_demanda.pkl` foi treinado.

Conteúdo de `IA aplicada.zip`:

- **`Treinamento_Modelo_Demanda_Sprint3.ipynb`** — notebook de treino do RandomForest, com dados reais da planilha SP2 (60 sessões).
- **`grafico_comparativo.png`** — gráfico comparando a previsão do modelo treinado com o dicionário de tarifas fixo (fallback).
- **`modelo_demanda.pkl`** — cópia do modelo treinado. O arquivo que o sistema de fato carrega em tempo de execução é `entregas/modelo_demanda.pkl` (mesmo conteúdo, mantido lá pra ficar junto do código que o usa).
