"""
api_server.py — Camada HTTP para o Dashboard (Luan)
GoodWe Challenge - ChargeGrid Intelligence

Este arquivo NÃO altera a lógica de negócio do Raul (ev_chargegrid.py).
Ele só expõe, via Flask, as mesmas funções que existiam para uso em
console: iniciar_sessao, encerrar_sessao, simular_tempo, painel_operacional
etc. viram rotas JSON, para o front-end (HTML/CSS/JS) consumir com fetch().

Por que precisa existir:
  - ev_chargegrid.py usa input()/print(), não dá pra chamar de um browser.
  - potencia_kw de cada estação só existe na memória do processo (não é
    salvo no banco), então o servidor precisa manter esse processo vivo
    para o dashboard mostrar kW em tempo real.

Como rodar:
  cd backend
  pip install -r requirements.txt
  python api_server.py
  -> API sobe em http://localhost:5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import os
import sys
import threading
import time

# ev_chargegrid.py mora em entregas/, uma pasta acima deste arquivo — sem
# isso o import falha com ModuleNotFoundError quando rodado a partir daqui.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_chargegrid as cg

app = Flask(__name__)
CORS(app)  # permite o front (arquivo estático / outra porta) chamar a API

cg.inicializar_banco()

# ─── Loop automático de simulação (+30min a cada N segundos reais) ───────────
# Correção do requisito "consumo acumulado no dia" / "receita em tempo real":
# sem isso, kwh_consumidos e valor_sessao só subiam se alguém chamasse
# simular_tempo() manualmente. Agora o próprio servidor avança o relógio
# sozinho, como um sistema de verdade rodaria.
SIMULACAO_INTERVALO_SEGUNDOS = 15  # 15s reais = +30min simulados

def _loop_simulacao():
    while True:
        time.sleep(SIMULACAO_INTERVALO_SEGUNDOS)
        if cg.contar_ativas() > 0:
            cg.simular_tempo()

threading.Thread(target=_loop_simulacao, daemon=True).start()

# Timestamp real de início de cada sessão (só existe aqui na API, não no
# backend original — o Raul só guarda a hora 0-23, não o instante exato).
# Usado pelo totem para mostrar "tempo decorrido" em minutos/segundos.
_INICIO_REAL = {}


# ─── Helpers de serialização ──────────────────────────────────────────────────

def estacao_para_dict(e: "cg.SessaoRecarga") -> dict:
    return {
        "estacao": e.id_estacao,
        "status": "Ocupada" if e.ativa else "Livre",
        "usuario": e.id_usuario,
        "potencia_kw": round(e.potencia_kw, 2),
        "kwh_consumidos": round(e.kwh_consumidos, 2),
        "hora_inicio": e.hora_inicio,
        "valor_sessao": round(e.valor_sessao, 2),
        "metodo_pagamento": e.metodo_pagamento,
    }


# ─── Rotas de leitura (painel principal) ──────────────────────────────────────

@app.get("/api/painel")
def painel():
    """
    Monta o painel usando, sempre que possível, as funções de leitura
    OFICIAIS do Raul (listar_sessoes_ativas, obter_status_estacoes) mais a
    obter_potencia_estacoes (nova, 5ª função). O único campo que ainda não
    tem uma leitura oficial é 'hora_inicio' — lido direto do objeto em
    memória, sinalizado abaixo, até existir uma função pra isso também.
    """
    hora_atual = datetime.datetime.now().hour

    status_por_estacao = cg.obter_status_estacoes()          # oficial (Raul)
    potencia_por_estacao = cg.obter_potencia_estacoes()       # oficial (novo)
    sessoes_ativas = {s["estacao"]: s for s in cg.listar_sessoes_ativas()}  # oficial (Raul)

    estacoes_out = []
    for n in range(1, cg.MAX_ESTACOES + 1):
        info = sessoes_ativas.get(n)
        ativa = status_por_estacao[n] == "Ocupada"
        estacoes_out.append({
            "estacao": n,
            "status": status_por_estacao[n],
            "usuario": info["usuario"] if info else "LIVRE",
            "potencia_kw": potencia_por_estacao.get(n, 0.0),
            "kwh_consumidos": round(info["kwh"], 2) if info else 0.0,
            "valor_sessao": round(info["valor"], 2) if info else 0.0,
            "metodo_pagamento": info["pagamento"] if info else "---",
            # ainda não coberto por uma função de leitura oficial:
            "hora_inicio": cg.estacoes[n - 1].hora_inicio if ativa else 0,
            "iniciado_em_real": _INICIO_REAL.get(n) if ativa else None,
        })

    return jsonify({
        "estacoes": estacoes_out,
        "ativas": cg.contar_ativas(),
        "max_estacoes": cg.MAX_ESTACOES,
        "potencia_usada_kw": round(sum(potencia_por_estacao.values()), 2),
        "limite_potencia_grid_kw": cg.LIMITE_POTENCIA_GRID,
        "receita_total": round(cg.receita_total, 2),
        "consumo_total_diario_kwh": round(cg.consumo_total_diario, 2),
        "hora_atual": hora_atual,
        "demanda_ia_agora": round(cg.ia_prever_demanda(hora_atual), 2),
        "atualizado_em": datetime.datetime.now().isoformat(),
    })


@app.get("/api/kpis")
def kpis():
    return jsonify({
        "faturamento_dia": cg.obter_faturamento_dia(),
        "sessoes_dia": cg.contar_sessoes_dia(),
        "sessoes_ativas": cg.listar_sessoes_ativas(),
        "status_estacoes": cg.obter_status_estacoes(),
    })


@app.get("/api/demanda-ia")
def demanda_ia():
    """Curva de demanda prevista pela IA, hora a hora (0-23h) — para gráfico."""
    curva = [{"hora": h, "demanda": round(cg.ia_prever_demanda(h), 2)} for h in range(24)]
    return jsonify(curva)


# ─── Rotas de ação (equivalentes às opções do menu de console) ───────────────

@app.post("/api/sessoes/iniciar")
def api_iniciar_sessao():
    dados = request.get_json(force=True) or {}
    idx = int(dados.get("estacao", 0)) - 1
    uid = (dados.get("usuario") or "ANONIMO").strip().upper()
    hora = dados.get("hora", datetime.datetime.now().hour)
    pagamento = dados.get("pagamento") or "App"

    if not (0 <= idx < cg.MAX_ESTACOES):
        return jsonify({"erro": "Estação inexistente."}), 400
    if cg.estacoes[idx].ativa:
        return jsonify({"erro": "Estação já ocupada."}), 409
    if uid != "ANONIMO" and not cg.validar_usuario(uid):
        return jsonify({"erro": f"Credencial '{uid}' não autorizada."}), 403

    try:
        hora = int(hora)
        if not (0 <= hora <= 23):
            hora = datetime.datetime.now().hour
    except (TypeError, ValueError):
        hora = datetime.datetime.now().hour

    uid_mascarado = cg.mascarar_id(uid)
    data_hoje = datetime.date.today().isoformat()

    import sqlite3
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessoes
            (id_estacao, usuario, data_sessao, hora_inicio, metodo_pagamento, status_pagamento, ativa)
        VALUES (?, ?, ?, ?, ?, 'PENDENTE', 1)
    """, (idx + 1, uid_mascarado, data_hoje, hora, pagamento))
    id_gerado_db = cursor.lastrowid
    conn.commit()
    conn.close()

    e = cg.estacoes[idx]
    e.id_usuario = uid_mascarado
    e.hora_inicio = hora
    e.ativa = True
    e.metodo_pagamento = pagamento
    e.id_sessao_db = id_gerado_db
    _INICIO_REAL[idx + 1] = datetime.datetime.now().isoformat()

    cg.ocpp_enviar("StartTransaction", e.id_estacao, {"status": "Connected", "usuario": uid_mascarado})
    cg.balancear_carga()

    return jsonify({"ok": True, "estacao": estacao_para_dict(e)})


@app.post("/api/sessoes/<int:estacao_num>/encerrar")
def api_encerrar_sessao(estacao_num: int):
    idx = estacao_num - 1
    if not (0 <= idx < cg.MAX_ESTACOES) or not cg.estacoes[idx].ativa:
        return jsonify({"erro": "Estação inativa ou inexistente."}), 400

    e = cg.estacoes[idx]
    cobranca = cg.criar_pagamento_sandbox(e.valor_sessao, e.id_sessao_db)
    recibo = estacao_para_dict(e)
    recibo["checkout_url"] = cobranca["url"]
    recibo["transacao_id"] = cobranca["transacao_id"]

    cg.confirmar_pagamento(e.id_sessao_db)
    cg.receita_total += e.valor_sessao
    cg.ocpp_enviar("StopTransaction", e.id_estacao, {"status": "Disconnected", "usuario": e.id_usuario})
    e.encerrar()
    cg.balancear_carga()
    _INICIO_REAL.pop(estacao_num, None)

    return jsonify({"ok": True, "recibo": recibo})


@app.post("/api/tempo/avancar")
def api_avancar_tempo():
    """Equivalente à opção 2 do menu: avança +30min de simulação."""
    cg.simular_tempo()
    return jsonify({"ok": True, "painel": painel().json})


@app.post("/api/usuarios")
def api_cadastrar_usuario():
    dados = request.get_json(force=True) or {}
    placa = (dados.get("placa") or "").strip()
    nome = dados.get("nome") or "Usuario Cadastrado"
    if not placa:
        return jsonify({"erro": "Placa é obrigatória."}), 400
    novo = cg.cadastrar_usuario(placa, nome)
    return jsonify({"ok": True, "cadastrado_agora": novo})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
