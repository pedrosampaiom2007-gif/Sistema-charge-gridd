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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime
import os
import secrets
import sys
import threading
import time

# ev_chargegrid.py mora em entregas/, uma pasta acima deste arquivo — sem
# isso o import falha com ModuleNotFoundError quando rodado a partir daqui.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_chargegrid as cg
import chatbot

app = Flask(__name__)

# ─── CORS — allowlist, não wildcard ───────────────────────────────────────────
# As 3 telas (totem, app, dashboard) hoje são abertas direto como arquivo
# (file://), e por isso o navegador manda Origin: null nas chamadas fetch —
# sem incluir "null" aqui, travar o CORS quebraria o app do jeito que ele é
# usado hoje. Em produção, defina CORS_ORIGINS com as URLs reais (separadas
# por vírgula) e "null" deixa de ser necessário se os front-ends passarem a
# ser servidos por HTTP em vez de abertos como arquivo local.
_origens_env = os.environ.get("CORS_ORIGINS", "")
_ORIGENS_PERMITIDAS = [o.strip() for o in _origens_env.split(",") if o.strip()] or [
    "null",
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:5173", "http://127.0.0.1:5173",
]
CORS(app, origins=_ORIGENS_PERMITIDAS)

# ─── Rate limiting — por IP ────────────────────────────────────────────────────
# Guarda em memória do processo (suficiente pra 1 worker; um deploy com vários
# workers/instâncias precisaria de um storage compartilhado, ex. Redis).
limiter = Limiter(get_remote_address, app=app, default_limits=["300 per minute"])

# ─── Cabeçalhos de segurança em toda resposta ─────────────────────────────────
@app.after_request
def _cabecalhos_seguranca(resp):
    resp.headers["X-Frame-Options"] = "DENY"           # clickjacking
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp

cg.inicializar_banco()

# ─── Recupera sessões que ficaram ativas no banco de uma execução anterior ────
# Sem isso, toda vez que o processo reinicia (deploy, reboot, o próprio
# reloader do Flask), a memória "esquece" que uma estação estava ocupada,
# mesmo que o banco ainda mostre a sessão como ativa — permitindo iniciar uma
# segunda sessão na mesma estação física e duplicar a linha no banco.
def _recuperar_sessoes_ativas():
    with cg.conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, id_estacao, usuario, hora_inicio, kwh_consumidos, valor_sessao, metodo_pagamento
            FROM sessoes WHERE ativa = 1 ORDER BY id_estacao, id DESC
        """)
        vistas = set()
        for id_db, id_estacao, usuario, hora_inicio, kwh, valor, pagamento in cursor.fetchall():
            if id_estacao in vistas:
                # sessão duplicada/travada de uma execução anterior — fecha, não é real
                cursor.execute("UPDATE sessoes SET ativa = 0 WHERE id = %s", (id_db,))
                continue
            vistas.add(id_estacao)
            e = cg.estacoes[id_estacao - 1]
            e.id_usuario = usuario
            e.hora_inicio = hora_inicio
            e.ativa = True
            e.kwh_consumidos = kwh
            e.valor_sessao = valor
            e.metodo_pagamento = pagamento
            e.id_sessao_db = id_db
    if vistas:
        cg.balancear_carga()
        print(f"[RECUPERACAO] {len(vistas)} sessão(ões) ativa(s) recuperada(s) do banco: estações {sorted(vistas)}")

_recuperar_sessoes_ativas()

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

# Tokens de sessão do admin — em memória, como o resto do estado "ao vivo"
# deste servidor. Válidos até o processo reiniciar (mesma limitação que já
# existe pra potencia_kw). Suficiente pra uma demonstração; um sistema de
# produção usaria algo com expiração e persistência.
_TOKENS_ADMIN_VALIDOS = set()


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

    # Uma consulta só ao banco: antes, obter_status_estacoes() chamava
    # listar_sessoes_ativas() por dentro e a linha de baixo chamava de novo —
    # duas idas ao Postgres por requisição, no endpoint que o totem e o
    # dashboard consultam a cada 3-4 segundos.
    lista_sessoes_ativas = cg.listar_sessoes_ativas()         # oficial (Raul)
    status_por_estacao = cg.status_das_sessoes(lista_sessoes_ativas)
    potencia_por_estacao = cg.obter_potencia_estacoes()       # oficial (novo)
    sessoes_ativas = {s["estacao"]: s for s in lista_sessoes_ativas}

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

    # Sem receita_total nem consumo_total_diario_kwh aqui: esta rota é aberta
    # (o totem, que não tem login, depende dela) e esses dois são número de
    # negócio somando TODOS os clientes — mesma natureza do que /api/kpis já
    # protege. Foram pra lá; o dashboard, que é logado, lê de lá.
    return jsonify({
        "estacoes": estacoes_out,
        "ativas": cg.contar_ativas(),
        "max_estacoes": cg.MAX_ESTACOES,
        "potencia_usada_kw": round(sum(potencia_por_estacao.values()), 2),
        "limite_potencia_grid_kw": cg.LIMITE_POTENCIA_GRID,
        "hora_atual": hora_atual,
        "demanda_ia_agora": round(cg.ia_prever_demanda(hora_atual), 2),
        "atualizado_em": datetime.datetime.now().isoformat(),
    })


def _token_admin_valido() -> bool:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return token in _TOKENS_ADMIN_VALIDOS


@app.get("/api/kpis")
def kpis():
    if not _token_admin_valido():
        return jsonify({"erro": "Login de administrador necessário."}), 401
    sessoes_ativas = cg.listar_sessoes_ativas()
    return jsonify({
        "faturamento_dia": cg.obter_faturamento_dia(),
        "sessoes_dia": cg.contar_sessoes_dia(),
        "sessoes_ativas": sessoes_ativas,
        "status_estacoes": cg.status_das_sessoes(sessoes_ativas),
        # vieram do /api/painel (aberto) pra cá: são agregados do negócio,
        # não estado da estação que o totem precisa ver.
        "receita_total": round(cg.receita_total, 2),
        "consumo_total_diario_kwh": round(cg.consumo_total_diario, 2),
    })


@app.get("/api/demanda-ia")
def demanda_ia():
    """Curva de demanda prevista pela IA, hora a hora (0-23h) — para gráfico."""
    if not _token_admin_valido():
        return jsonify({"erro": "Login de administrador necessário."}), 401
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
    # Vincula a sessão à CONTA, não só à placa mascarada — é o que faz o
    # histórico de pagamento apontar pro dono certo (ver historico_usuario).
    conta_id = cg.conta_da_placa(uid)

    with cg.conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessoes
                (id_estacao, usuario, data_sessao, hora_inicio, metodo_pagamento, status_pagamento, ativa, conta_id)
            VALUES (%s, %s, %s, %s, %s, 'PENDENTE', 1, %s)
            RETURNING id
        """, (idx + 1, uid_mascarado, data_hoje, hora, pagamento, conta_id))
        id_gerado_db = cursor.fetchone()[0]

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
    """Equivalente à opção 2 do menu: avança +30min de simulação.

    Exige login de administrador: essa rota MEXE EM DINHEIRO — cada chamada
    soma kWh e reais em toda sessão ativa, ou seja, na conta que o motorista
    vai pagar no fim. Sem login, qualquer um com a URL da API podia inflar a
    fatura de todo mundo em looping. Nenhuma das três telas usa essa rota (o
    próprio servidor avança o tempo sozinho, ver _loop_simulacao) — ela existe
    como controle manual de demonstração."""
    if not _token_admin_valido():
        return jsonify({"erro": "Login de administrador necessário."}), 401
    cg.simular_tempo()
    return jsonify({"ok": True, "painel": painel().json})


def _pin_valido(pin: str) -> bool:
    return isinstance(pin, str) and pin.isdigit() and len(pin) == 4


@app.post("/api/usuarios")
@limiter.limit("10 per minute")
def api_cadastrar_usuario():
    dados = request.get_json(force=True) or {}
    placa = (dados.get("placa") or "").strip()
    nome = dados.get("nome") or "Usuario Cadastrado"
    pin = (dados.get("pin") or "").strip()
    if not placa:
        return jsonify({"erro": "Placa é obrigatória."}), 400
    if not _pin_valido(pin):
        return jsonify({"erro": "PIN precisa ter exatamente 4 números."}), 400
    novo = cg.cadastrar_usuario(placa, nome, pin)
    return jsonify({"ok": True, "cadastrado_agora": novo})


@app.post("/api/usuarios/historico")
@limiter.limit("20 per minute")
def api_historico_usuario():
    """Histórico de pagamentos do motorista — todas as sessões de TODAS as
    placas vinculadas à mesma conta dessa placa (motorista com mais de um
    carro), mais recentes primeiro. Usado pela tela 'meus pagamentos'.

    Exige o PIN da conta (definido no cadastro) — sem isso, bastava saber a
    placa (sem segredo nenhum) pra ver o histórico de pagamento de qualquer
    motorista (IDOR, já foi assim antes desta correção). É por isso que essa
    rota é POST com o PIN no corpo, não mais GET só com a placa na URL.
    """
    dados = request.get_json(force=True) or {}
    placa = (dados.get("placa") or "").strip()
    pin = (dados.get("pin") or "").strip()
    if not placa or not pin:
        return jsonify({"erro": "Informe a placa e o PIN."}), 400
    if not cg.validar_pin(placa, pin):
        return jsonify({"erro": "Placa ou PIN incorretos."}), 403
    return jsonify({"placa": placa.strip().upper(), "sessoes": cg.historico_usuario(placa)})


@app.post("/api/usuarios/vincular")
def api_vincular_placa():
    """Adiciona um segundo (ou terceiro...) carro à mesma conta de uma
    placa já cadastrada — exige o PIN da conta como prova de que quem
    está pedindo é o dono, não só alguém que sabe a placa existente."""
    dados = request.get_json(force=True) or {}
    placa_existente = (dados.get("placa_existente") or "").strip()
    placa_nova = (dados.get("placa_nova") or "").strip()
    pin = (dados.get("pin") or "").strip()
    if not placa_existente or not placa_nova or not pin:
        return jsonify({"erro": "Informe a placa atual, o PIN e a nova placa."}), 400
    ok = cg.vincular_placa(placa_existente, placa_nova, pin)
    if not ok:
        return jsonify({"erro": "Não foi possível vincular. Confira a placa atual, o PIN, e se a nova placa já não está em uso."}), 400
    return jsonify({"ok": True})


# ─── Login de administrador ────────────────────────────────────────────────
# Separado do login por placa: o motorista "loga" digitando a placa (já
# existia); o gestor precisa de usuário+senha de verdade, porque enxerga
# dado agregado (faturamento total, curva de demanda) que não é do
# motorista ver. Ver README para trocar a senha padrão antes de usar de
# verdade — a de teste (admin / chargegrid2026) é só pra desenvolvimento.

# Bloqueio por CONTA, além do limite por IP (@limiter.limit abaixo) — um
# ataque distribuído por vários IPs contra o mesmo usuário passaria batido
# só com limite por IP. Em memória do processo, mesma limitação já aceita
# pra _TOKENS_ADMIN_VALIDOS.
_FALHAS_LOGIN_POR_CONTA: dict[str, list[float]] = {}
_JANELA_BLOQUEIO_SEGUNDOS = 300
_MAX_FALHAS_POR_CONTA = 5

def _conta_bloqueada(usuario: str) -> bool:
    agora = time.time()
    tentativas = [t for t in _FALHAS_LOGIN_POR_CONTA.get(usuario, []) if agora - t < _JANELA_BLOQUEIO_SEGUNDOS]
    _FALHAS_LOGIN_POR_CONTA[usuario] = tentativas
    return len(tentativas) >= _MAX_FALHAS_POR_CONTA

def _registrar_falha_login(usuario: str) -> None:
    _FALHAS_LOGIN_POR_CONTA.setdefault(usuario, []).append(time.time())


@app.post("/api/admin/login")
@limiter.limit("5 per minute")
def api_admin_login():
    dados = request.get_json(force=True) or {}
    usuario = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""

    if _conta_bloqueada(usuario):
        return jsonify({"erro": "Muitas tentativas para este usuário. Aguarde alguns minutos e tente de novo."}), 429

    if not cg.validar_admin(usuario, senha):
        _registrar_falha_login(usuario)
        return jsonify({"erro": "Usuário ou senha inválidos."}), 403

    _FALHAS_LOGIN_POR_CONTA.pop(usuario, None)
    token = secrets.token_hex(16)
    _TOKENS_ADMIN_VALIDOS.add(token)
    return jsonify({"ok": True, "token": token})


@app.post("/api/admin/logout")
def api_admin_logout():
    """Revoga o token no servidor — sem isso, um token continuava válido pra
    sempre (até a API reiniciar) mesmo depois do usuário "sair" no front."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    _TOKENS_ADMIN_VALIDOS.discard(token)
    return jsonify({"ok": True})


# ─── Chatbot ────────────────────────────────────────────────────────────────

@app.post("/api/chat")
@limiter.limit("15 per minute")
def api_chat():
    """Quem pergunta define o que o chat enxerga:

      - com token de admin  -> acesso de gestão: faturamento, sessões do dia,
        histórico de receita. Mesma fronteira do /api/kpis.
      - com placa + PIN     -> motorista logado: o gasto PESSOAL dele, mais
        disponibilidade de estação e dúvidas gerais de carro elétrico.
      - sem nada            -> só disponibilidade de estação e dúvidas gerais.

    O padrão é o MAIS restrito de propósito. Antes era o contrário: o acesso
    de gestão era o padrão e a restrição só ligava quando o motorista se
    identificava — ou seja, bastava chamar /api/chat sem placa nenhuma pra
    receber o faturamento do sistema. Quem se identificava via menos que um
    anônimo.

    O gasto pessoal exige o mesmo PIN do histórico: sem isso, dava pra usar o
    chat pra contornar a checagem que /api/usuarios/historico já faz."""
    dados = request.get_json(force=True) or {}
    pergunta = (dados.get("pergunta") or "").strip()
    placa = (dados.get("placa") or "").strip()
    pin = (dados.get("pin") or "").strip()
    if not pergunta:
        return jsonify({"erro": "Pergunta é obrigatória."}), 400

    acesso_gestao = _token_admin_valido()
    contexto_extra = None

    if placa and pin:
        if not cg.validar_pin(placa, pin):
            return jsonify({"erro": "Placa ou PIN incorretos."}), 403
        sessoes = cg.historico_usuario(placa)
        total_pessoal = sum(s["valor"] for s in sessoes)
        contexto_extra = (
            f"[GASTO PESSOAL DO MOTORISTA LOGADO — placa {placa.upper()}] "
            f"Total já gasto por esse motorista em {len(sessoes)} sessão(ões): "
            f"R$ {total_pessoal:.2f}. Isso é o gasto individual DESSE motorista, "
            f"diferente do faturamento/receita total do sistema (que soma todos "
            f"os clientes)."
        )

    try:
        resposta = chatbot.responder(
            pergunta,
            contexto_extra=contexto_extra,
            acesso_gestao=acesso_gestao,
        )
    except Exception as e:
        return jsonify({"erro": f"Chatbot indisponível: {e}"}), 503
    return jsonify({"resposta": resposta})


if __name__ == "__main__":
    # FLASK_DEBUG=1 só em desenvolvimento local — debug=True liga o debugger
    # interativo do Werkzeug, que permite execução remota de código se a API
    # ficar exposta publicamente (deploy). PORT vem do ambiente (Render/
    # Railway definem isso sozinhos); 5000 é só o padrão local.
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug, port=port, host="0.0.0.0")
