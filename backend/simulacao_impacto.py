"""
simulacao_impacto.py - simulacao de impacto do ChargeGrid Intelligence
EV Challenge 2026 - GoodWe / FIAP

O que este arquivo é (e o que nao é):
  Uma SIMULACAO, nao uma medicao. O sistema nao tem inversor, carregador
  nem bateria reais conectados, entao nao da pra medir CO2 evitado de
  verdade. O que da pra fazer, e é o que este script faz, é estimar o efeito
  da tarifa dinamica e de uma bateria usando duas coisas:
    1) o perfil por hora das 60 sessoes reais da base (chatbot/dados_rag.json);
    2) premissas escritas aqui embaixo, que qualquer um pode trocar e rodar
       de novo.
  Os resultados dependem dessas premissas. Nenhuma delas veio de medicao
  feita pelo grupo.

Como rodar:
  python simulacao_impacto.py            (so a tabela no terminal)
  python simulacao_impacto.py --grafico  (tambem salva simulacao_impacto.png)
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SESSOES = os.path.join(BASE, "..", "chatbot", "dados_rag.json")

# ---------------------------------------------------------------------------
# Premissas (troque aqui e rode de novo)
# ---------------------------------------------------------------------------

# Mesma curva sintética de backend/solar_optimizer.py (_CURVA_FALLBACK):
# fracao da geracao maxima do dia, hora a hora.
CURVA_SOLAR = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.02,
    0.08, 0.20, 0.38, 0.58, 0.76, 0.90,
    0.98, 1.00, 0.95, 0.82, 0.62, 0.40,
    0.18, 0.05, 0.00, 0.00, 0.00, 0.00,
]
TAMANHO_JANELA_SOLAR = 4          # igual ao solar_optimizer.py
HORAS_PICO = (18, 19, 20)         # HORA_INICIO_PICO..HORA_FIM_PICO do motor
HORAS_MADRUGADA = tuple(range(0, 6))

# Fatores de tarifa que dependem so do horario (ev_chargegrid.ia_calcular_tarifa).
# Ocupacao e previsao da IA tambem entram na tarifa real, mas ficam de fora
# aqui pra isolar o efeito do horario.
FATOR_PICO = 1.30
FATOR_SOLAR = 0.90
FATOR_MADRUGADA = 0.80

# Duracao media de uma sessao na base: 2,58 h. Arredondada pra 3 h: a energia
# de cada sessao e espalhada em 3 horas a partir da hora de inicio.
DURACAO_SESSAO_H = 3

# Quanto da recarga do pico migraria pra janela solar por causa do desconto.
# NAO ha dado de comportamento real do motorista: e um cenario, nao previsao.
FRACOES_DESLOCAMENTO = (0.10, 0.20, 0.30)
FRACAO_PADRAO = 0.20

# Estacionamento hipotetico, so pra dar escala em kWh (premissas do grupo).
SESSOES_POR_DIA = 20
PV_KWP = 50.0                     # potencia instalada de paineis
PV_PRODUCAO_KWH_POR_KWP_DIA = 4.5 # premissa tipica de Sao Paulo
BATERIA_KWH = 100.0               # capacidade util
BATERIA_EFIC_CARGA = 0.95         # carga e descarga: 0,95 * 0,95 = 0,90 de ida e volta
BATERIA_EFIC_DESCARGA = 0.95

# Fatores de emissao em kg CO2 por kWh (= tCO2/MWh).
#  - Media da rede: 0,0289, MCTI, abril/2025 (via Cenario Energia).
#  - Termica a gas (ciclo combinado), ciclo de vida: 0,490, IPCC AR5, Anexo III.
#  - Solar fotovoltaica de telhado, ciclo de vida: 0,041, IPCC AR5, Anexo III.
EF_REDE_MEDIA = 0.0289
EF_GAS = 0.490
EF_SOLAR = 0.041


# ---------------------------------------------------------------------------
# Perfil de carga das 60 sessoes
# ---------------------------------------------------------------------------

def carregar_perfil_base():
    """kWh por hora do dia (lista de 24), somando as 60 sessoes reais.
    A energia de cada sessao é dividida igualmente nas DURACAO_SESSAO_H horas
    seguintes ao inicio (volta pra 0h depois das 23h)."""
    with open(ARQUIVO_SESSOES, encoding="utf-8") as f:
        dados = json.load(f)
    perfil = [0.0] * 24
    for linha in dados["sessoes_por_hora"]:
        energia = linha["total_sessoes"] * linha["consumo_medio_kwh"]
        for i in range(DURACAO_SESSAO_H):
            perfil[(linha["hora"] + i) % 24] += energia / DURACAO_SESSAO_H
    return perfil


def escalar(perfil, total):
    soma = sum(perfil)
    return [x * total / soma for x in perfil]


def janela_solar():
    ordem = sorted(range(24), key=lambda h: CURVA_SOLAR[h], reverse=True)
    return sorted(ordem[:TAMANHO_JANELA_SOLAR])


def fator_tarifa(h, janela):
    if h in HORAS_PICO:
        return FATOR_PICO
    if h in HORAS_MADRUGADA:
        return FATOR_MADRUGADA
    if h in janela:
        return FATOR_SOLAR
    return 1.0


def deslocar(perfil, fracao, janela):
    """Move `fracao` da energia de cada hora de pico, em partes iguais,
    pras horas da janela solar."""
    novo = list(perfil)
    movido = 0.0
    for h in HORAS_PICO:
        tira = perfil[h] * fracao
        novo[h] -= tira
        movido += tira
    for h in janela:
        novo[h] += movido / len(janela)
    return novo, movido


# ---------------------------------------------------------------------------
# Parte 1: efeito da tarifa por horario
# ---------------------------------------------------------------------------

def resumo_periodos(perfil, janela):
    total = sum(perfil)
    pico = sum(perfil[h] for h in HORAS_PICO)
    solar = sum(perfil[h] for h in janela)
    madr = sum(perfil[h] for h in HORAS_MADRUGADA)
    return {
        "pico_pct": 100 * pico / total,
        "janela_solar_pct": 100 * solar / total,
        "madrugada_pct": 100 * madr / total,
        "outras_pct": 100 * (total - pico - solar - madr) / total,
        "hora_mais_carregada": max(range(24), key=lambda h: perfil[h]),
        "pct_hora_mais_carregada": 100 * max(perfil) / total,
    }


def parte_tarifa(perfil_base, janela):
    total = sum(perfil_base)
    fator_base = sum(perfil_base[h] * fator_tarifa(h, janela) for h in range(24)) / total
    saida = {"base": resumo_periodos(perfil_base, janela), "cenarios": {}}
    for fr in FRACOES_DESLOCAMENTO:
        novo, movido = deslocar(perfil_base, fr, janela)
        fator_novo = sum(novo[h] * fator_tarifa(h, janela) for h in range(24)) / total
        saida["cenarios"][fr] = {
            "energia_movida_pct_do_dia": 100 * movido / total,
            "fator_medio_base": fator_base,
            "fator_medio_novo": fator_novo,
            "conta_menor_pct": 100 * (1 - fator_novo / fator_base),
            "pct_hora_mais_carregada": 100 * max(novo) / total,
            "preco_kwh_movido_menor_pct": 100 * (1 - FATOR_SOLAR / FATOR_PICO),
        }
    return saida


# ---------------------------------------------------------------------------
# Parte 2: paineis + bateria num estacionamento hipotetico
# ---------------------------------------------------------------------------

def geracao_pv():
    """kWh gerados por hora, escalados pra producao diaria da premissa."""
    soma = sum(CURVA_SOLAR)
    alvo = PV_KWP * PV_PRODUCAO_KWH_POR_KWP_DIA
    return [c * alvo / soma for c in CURVA_SOLAR]


def simular_dia(carga, usar_pv, usar_bateria):
    """Devolve (importacao da rede por hora, energia solar usada direto,
    energia entregue pela bateria). Bateria comeca vazia, carrega so com a
    sobra solar e so descarrega nas horas de pico."""
    pv = geracao_pv() if usar_pv else [0.0] * 24
    soc = 0.0
    rede = [0.0] * 24
    solar_direto = 0.0
    da_bateria = 0.0
    for h in range(24):
        direto = min(carga[h], pv[h])
        sobra = pv[h] - direto
        falta = carga[h] - direto
        solar_direto += direto
        if usar_bateria and sobra > 0:
            cabe = (BATERIA_KWH - soc) / BATERIA_EFIC_CARGA
            entra = min(sobra, cabe)
            soc += entra * BATERIA_EFIC_CARGA
        if usar_bateria and h in HORAS_PICO and falta > 0 and soc > 0:
            entrega = min(falta, soc * BATERIA_EFIC_DESCARGA)
            soc -= entrega / BATERIA_EFIC_DESCARGA
            da_bateria += entrega
            falta -= entrega
        rede[h] = falta
    return rede, solar_direto, da_bateria


def co2_kg(rede, solar_direto, da_bateria, ponta_fossil):
    total = 0.0
    for h in range(24):
        if ponta_fossil and h in HORAS_PICO:
            total += rede[h] * EF_GAS
        else:
            total += rede[h] * EF_REDE_MEDIA
    total += (solar_direto + da_bateria) * EF_SOLAR
    return total


def parte_bateria(perfil_base, janela):
    energia_dia = SESSOES_POR_DIA * carregar_media_sessao()
    carga_base = escalar(perfil_base, energia_dia)
    carga_desl, _ = deslocar(carga_base, FRACAO_PADRAO, janela)

    casos = [
        ("Sem nada (so a rede)", carga_base, False, False),
        ("Tarifa desloca 20% do pico", carga_desl, False, False),
        ("Paineis", carga_base, True, False),
        ("Paineis + bateria", carga_base, True, True),
        ("Paineis + bateria + tarifa", carga_desl, True, True),
    ]
    base_rede, _, _ = simular_dia(carga_base, False, False)
    base_pico = sum(base_rede[h] for h in HORAS_PICO)
    base_total = sum(base_rede)
    base_co2 = {
        "media": co2_kg(base_rede, 0, 0, False),
        "ponta_fossil": co2_kg(base_rede, 0, 0, True),
    }

    saida = {"energia_dia_kwh": energia_dia, "casos": []}
    for nome, carga, pv, bat in casos:
        rede, direto, da_bat = simular_dia(carga, pv, bat)
        pico = sum(rede[h] for h in HORAS_PICO)
        total_rede = sum(rede)
        co2_m = co2_kg(rede, direto, da_bat, False)
        co2_f = co2_kg(rede, direto, da_bat, True)
        saida["casos"].append({
            "nome": nome,
            "rede_total_kwh": total_rede,
            "rede_pico_kwh": pico,
            "rede_pico_menos_pct": 100 * (1 - pico / base_pico),
            "solar_no_total_pct": 100 * (direto + da_bat) / sum(carga),
            "da_bateria_kwh": da_bat,
            "co2_media_kg": co2_m,
            "co2_ponta_fossil_kg": co2_f,
            "co2_ponta_fossil_menos_pct": 100 * (1 - co2_f / base_co2["ponta_fossil"]),
            "co2_media_menos_pct": 100 * (1 - co2_m / base_co2["media"]),
            "rede_por_hora": rede,
            "carga_por_hora": carga,
        })
    saida["geracao_pv_kwh_dia"] = sum(geracao_pv())
    return saida


def carregar_media_sessao():
    with open(ARQUIVO_SESSOES, encoding="utf-8") as f:
        return json.load(f)["metricas_gerais"]["consumo_medio_kwh"]


# ---------------------------------------------------------------------------
# Saida
# ---------------------------------------------------------------------------

def imprimir(res_tarifa, res_bat, janela):
    b = res_tarifa["base"]
    print("PARTE 1 - tarifa por horario, com o perfil das 60 sessoes reais")
    print(f"  Janela solar usada: {janela[0]}h a {janela[-1]}h | pico: {HORAS_PICO[0]}h a {HORAS_PICO[-1]}h")
    print(f"  Energia no pico: {b['pico_pct']:.1f}% | na janela solar: {b['janela_solar_pct']:.1f}% | "
          f"madrugada: {b['madrugada_pct']:.1f}% | outras: {b['outras_pct']:.1f}%")
    print(f"  Hora mais carregada: {b['hora_mais_carregada']}h, com {b['pct_hora_mais_carregada']:.1f}% da energia do dia")
    for fr, c in res_tarifa["cenarios"].items():
        print(f"  Se {int(fr*100)}% da recarga do pico migrar pro sol: "
              f"{c['energia_movida_pct_do_dia']:.1f}% da energia do dia muda de horario, "
              f"hora mais carregada cai pra {c['pct_hora_mais_carregada']:.1f}%, "
              f"conta media {c['conta_menor_pct']:.1f}% menor "
              f"(cada kWh movido fica {c['preco_kwh_movido_menor_pct']:.0f}% mais barato)")
    print()
    print(f"PARTE 2 - estacionamento hipotetico: {SESSOES_POR_DIA} sessoes/dia = {res_bat['energia_dia_kwh']:.0f} kWh/dia, "
          f"{PV_KWP:.0f} kWp (gera {res_bat['geracao_pv_kwh_dia']:.0f} kWh/dia), bateria {BATERIA_KWH:.0f} kWh")
    cab = f"  {'Caso':<30}{'Rede (kWh)':>11}{'Rede pico':>11}{'Pico -%':>9}{'Solar %':>9}{'CO2 media':>11}{'CO2 ponta fossil':>18}"
    print(cab)
    for c in res_bat["casos"]:
        print(f"  {c['nome']:<30}{c['rede_total_kwh']:>11.0f}{c['rede_pico_kwh']:>11.0f}"
              f"{c['rede_pico_menos_pct']:>8.0f}%{c['solar_no_total_pct']:>8.0f}%"
              f"{c['co2_media_kg']:>9.1f} kg{c['co2_ponta_fossil_kg']:>11.1f} kg ({c['co2_ponta_fossil_menos_pct']:.0f}% menos)")


def desenhar(perfil, res_bat, janela):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    horas = list(range(24))
    total = sum(perfil)
    a1.bar(horas, [100 * x / total for x in perfil], color="#0F3D3E")
    a1.axvspan(HORAS_PICO[0] - .5, HORAS_PICO[-1] + .5, color="#F5A623", alpha=.35, label="pico (18h-20h)")
    a1.axvspan(janela[0] - .5, janela[-1] + .5, color="#7FC8A9", alpha=.35, label="janela solar")
    a1.set_title("Perfil das 60 sessoes reais")
    a1.set_xlabel("hora do dia")
    a1.set_ylabel("% da energia do dia")
    a1.legend()

    nomes = ["so a rede", "tarifa\n(20% do pico)", "paineis", "paineis\n+ bateria", "paineis\n+ bateria\n+ tarifa"]
    vals = [c["rede_pico_kwh"] for c in res_bat["casos"]]
    cores = ["#999999", "#F5A623", "#7FC8A9", "#2E8B8B", "#0F3D3E"]
    a2.bar(range(len(vals)), vals, color=cores)
    a2.set_xticks(range(len(vals)))
    a2.set_xticklabels(nomes, fontsize=7)
    a2.set_ylabel("kWh puxados da rede no pico (18h-20h)")
    a2.set_title("Simulacao: estacionamento hipotetico (premissas no codigo)")
    for i, v in enumerate(vals):
        a2.text(i, v + 1, f"{v:.0f}", ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(BASE, "simulacao_impacto.png"), dpi=150)


def main():
    perfil = carregar_perfil_base()
    janela = janela_solar()
    res_tarifa = parte_tarifa(perfil, janela)
    res_bat = parte_bateria(perfil, janela)
    imprimir(res_tarifa, res_bat, janela)

    saida_json = {
        "premissas": {
            "sessoes_por_dia": SESSOES_POR_DIA, "pv_kwp": PV_KWP,
            "pv_kwh_por_kwp_dia": PV_PRODUCAO_KWH_POR_KWP_DIA, "bateria_kwh": BATERIA_KWH,
            "ef_rede_media": EF_REDE_MEDIA, "ef_gas": EF_GAS, "ef_solar": EF_SOLAR,
            "fracao_padrao": FRACAO_PADRAO,
        },
        "tarifa": {str(k): v for k, v in res_tarifa["cenarios"].items()},
        "base": res_tarifa["base"],
        "bateria": [{k: v for k, v in c.items() if k not in ("rede_por_hora", "carga_por_hora")} for c in res_bat["casos"]],
    }
    with open(os.path.join(BASE, "simulacao_impacto_resultados.json"), "w", encoding="utf-8") as f:
        json.dump(saida_json, f, ensure_ascii=False, indent=2)

    if "--grafico" in sys.argv:
        desenhar(perfil, res_bat, janela)


if __name__ == "__main__":
    main()