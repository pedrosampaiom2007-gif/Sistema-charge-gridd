"""
solar_optimizer.py — previsão de geração solar e janela de incentivo à
recarga em horário de maior geração fotovoltaica.
EV Challenge 2026 — GoodWe / FIAP

O que isso é, com precisão (pra não prometer mais do que entrega):
  A previsão vem de uma API meteorológica pública (Open-Meteo, sem chave),
  não de um inversor GoodWe real conectado — não temos acesso a uma
  instalação GoodWe pra ler geração de verdade (a Open API SEMS da GoodWe
  existe, mas é liberada só por conta de organização + NDA com o time de
  vendas deles, ver docs/GOODWE_ROADMAP.md). Isso aqui é o primeiro
  degrau de um "solar-aware charging": reagir a uma PREVISÃO de sol, não
  ainda a uma LEITURA real do inversor.

Como isso vira desconto na tarifa:
  ev_chargegrid.ia_calcular_tarifa() chama esta_em_janela_solar(hora) e,
  se a hora estiver entre as de maior geração prevista pro dia (e não for
  hora de pico), aplica um desconto — mesmo mecanismo de incentivo que já
  existia pra madrugada, só que a janela aqui é calculada, não fixa: muda
  com a estação do ano e com o tempo (dia nublado desloca a janela).
"""

import os
import json
import datetime
import urllib.request

LATITUDE = float(os.environ.get("SOLAR_LATITUDE", "-23.5505"))    # São Paulo, ajustável por ambiente
LONGITUDE = float(os.environ.get("SOLAR_LONGITUDE", "-46.6333"))
TAMANHO_JANELA_SOLAR = 4     # nº de horas de maior geração prevista usadas como "janela"
TIMEOUT_SEGUNDOS = 4

# Perfil sintético (formato de sino, pico ao meio-dia) — usado só se a
# Open-Meteo não responder a tempo. Mesma filosofia do dicionário de
# fallback de demanda em ev_chargegrid.py: o recurso degrada, não quebra.
_CURVA_FALLBACK = {
     0: 0.00,  1: 0.00,  2: 0.00,  3: 0.00,  4: 0.00,  5: 0.02,
     6: 0.08,  7: 0.20,  8: 0.38,  9: 0.58, 10: 0.76, 11: 0.90,
    12: 0.98, 13: 1.00, 14: 0.95, 15: 0.82, 16: 0.62, 17: 0.40,
    18: 0.18, 19: 0.05, 20: 0.00, 21: 0.00, 22: 0.00, 23: 0.00,
}

# Cache por processo, uma consulta por dia — a previsão de manhã cedo não
# muda hora a hora o suficiente pra justificar bater na API pública a cada
# request (o /api/painel é consultado a cada 3-4s pelo totem e dashboard).
_cache_data = None
_cache_curva = None
_cache_fonte = None


def _buscar_curva_open_meteo() -> dict:
    """Consulta a Open-Meteo (gratuita, sem chave) e devolve
    {hora: fração 0.0-1.0 de geração relativa ao pico do dia}. Levanta
    exceção se a API não responder a tempo ou vier num formato inesperado
    — quem chama decide o fallback, esta função não esconde erro."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        "&hourly=shortwave_radiation&forecast_days=1&timezone=auto"
    )
    with urllib.request.urlopen(url, timeout=TIMEOUT_SEGUNDOS) as resp:
        dados = json.loads(resp.read().decode())

    horarios = dados["hourly"]["time"]              # ex: "2026-08-19T14:00"
    radiacao = dados["hourly"]["shortwave_radiation"]  # W/m², mesma ordem
    pico = max(radiacao) or 1  # evita divisão por zero num dia 100% nublado

    return {
        int(hora_iso[11:13]): round(valor / pico, 3)
        for hora_iso, valor in zip(horarios, radiacao)
    }


def curva_solar_hoje() -> dict:
    """{hora (0-23): fração 0.0-1.0} de geração prevista pra hoje."""
    global _cache_data, _cache_curva, _cache_fonte
    hoje = datetime.date.today().isoformat()

    if _cache_data == hoje and _cache_curva is not None:
        return _cache_curva

    try:
        curva = _buscar_curva_open_meteo()
        fonte = "open-meteo"
    except Exception:
        curva = dict(_CURVA_FALLBACK)
        fonte = "fallback"

    _cache_data, _cache_curva, _cache_fonte = hoje, curva, fonte
    return curva


def fonte_da_previsao() -> str:
    """'open-meteo' ou 'fallback' — pra deixar claro na API/UI quando a
    previsão real não estava disponível e o sistema caiu no perfil sintético."""
    curva_solar_hoje()  # garante que o cache do dia já foi populado
    return _cache_fonte


def janela_solar_hoje() -> set:
    """As TAMANHO_JANELA_SOLAR horas de maior geração prevista pra hoje."""
    curva = curva_solar_hoje()
    melhores = sorted(curva, key=curva.get, reverse=True)[:TAMANHO_JANELA_SOLAR]
    return set(melhores)


def esta_em_janela_solar(hora: int) -> bool:
    return hora in janela_solar_hoje()


def curva_solar_para_api() -> list:
    """Formato pronto pro /api/solar e o gráfico do dashboard: lista
    ordenada por hora, já marcando quais horas são a janela de incentivo."""
    curva = curva_solar_hoje()
    janela = janela_solar_hoje()
    return [
        {"hora": h, "geracao_relativa": curva.get(h, 0.0), "janela_solar": h in janela}
        for h in range(24)
    ]
