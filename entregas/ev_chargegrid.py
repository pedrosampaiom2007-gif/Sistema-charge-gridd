"""
ChargeGrid Intelligence — Plataforma de Gestão Comercial de Recarga EV
GoodWe Challenge - Sprint 3

Módulos Inseridos pelo Backend (Raul Sampaio):
  - Banco de Dados SQLite (chargegrid.db) integrado com persistência ao vivo.
  - Autenticação de Placas via Criptografia Hash (SHA-256).
  - Mascaramento de dados sensíveis em conformidade com diretrizes de privacidade.
  - Gateway de Pagamentos Integrado (Simulação Mercado Pago Sandbox API).

Ajustes adicionais (Sprint 3 — resolvidos a pedido do Pedro, sem custo e sem
complexidade extra):
  - Campo `data_sessao` na tabela `sessoes`, pra dar suporte a perguntas
    como "faturamento de hoje" (antes só existia hora_inicio, sem dia).
  - Pagamento Sandbox simplificado: por padrão roda 100% simulado local
    (sem precisar de credencial real, sem custo, sem travar em timeout de
    rede). Pode ser ligado para tentar a API real depois, via flag.
  - Cadastro dinâmico de usuário (placa), pra permitir testar com placas
    novas durante a demonstração sem editar o banco manualmente.
  - Funções de leitura prontas (listar_sessoes_ativas, obter_status_estacoes,
    obter_faturamento_dia, contar_sessoes_dia) — exatamente o que o README
    pedia pro Raul disponibilizar pra Lucas e Luan consumirem sem precisar
    escrever SQL ou tocar no motor principal.
"""

import json
import datetime
import sqlite3
import hashlib
import uuid
import requests
from dataclasses import dataclass
from typing import Optional

# ─── Constantes do sistema ────────────────────────────────────────────────────
MAX_ESTACOES          = 10      # pontos de recarga no estabelecimento comercial
LIMITE_POTENCIA_GRID  = 50.0    # kW — demanda contratada com a concessionária
MAX_POTENCIA_ESTACAO  = 22.0    # kW — limite por carregador AC (Tipo 2)
TARIFA_BASE_KWH       = 0.90    # R$/kWh — tarifa base comercial

# Flag de configuração do gateway de pagamento.
# Mantida em False por padrão: não exige cadastro externo, não gera custo
# e não depende de internet para a demonstração funcionar. Se o time
# conseguir credenciais reais de Sandbox do Mercado Pago, basta trocar
# para True.
USAR_API_REAL_MERCADOPAGO = False

# ─── IA: histórico de demanda por hora (padrão de uso comercial) ──────────────
DEMANDA_PREVISTA_POR_HORA = {
     0: 0.05,  1: 0.03,  2: 0.03,  3: 0.03,  4: 0.05,  5: 0.10,
     6: 0.20,  7: 0.45,  8: 0.70,  9: 0.80, 10: 0.85, 11: 0.90,
    12: 1.00, 13: 0.85, 14: 0.80, 15: 0.85, 16: 0.90, 17: 0.95,
    18: 1.00, 19: 1.00, 20: 0.95, 21: 0.80, 22: 0.55, 23: 0.25,
}


# ─── Sessão de recarga comercial ──────────────────────────────────────────────
@dataclass
class SessaoRecarga:
    """
    Representa uma sessão ativa em um ponto de recarga comercial.
    [RAUL]: Adicionado o campo id_sessao_db para vinculação relacional direta com o SQLite.
    """
    id_estacao:      int
    id_usuario:      str   = "LIVRE"   # Placa mascarada do motorista
    ativa:           bool  = False
    potencia_kw:     float = 0.0
    kwh_consumidos:  float = 0.0
    hora_inicio:     int   = 0
    valor_sessao:    float = 0.0
    metodo_pagamento: str  = "---"     # PIX, Cartão, App, QR Code
    id_sessao_db:    Optional[int] = None  # FK ID do SQLite para updates em tempo real

    def encerrar(self):
        self.id_usuario       = "LIVRE"
        self.ativa            = False
        self.potencia_kw      = 0.0
        self.kwh_consumidos   = 0.0
        self.hora_inicio      = 0
        self.valor_sessao     = 0.0
        self.metodo_pagamento = "---"
        self.id_sessao_db     = None


# ─── Estado do sistema ────────────────────────────────────────────────────────
estacoes: list[SessaoRecarga] = [
    SessaoRecarga(id_estacao=i + 1) for i in range(MAX_ESTACOES)
]
receita_total:         float = 0.0
consumo_total_diario:  float = 0.0


# ─── MÓDULO BACKEND: SEGURANÇA E PERSISTÊNCIA (RAUL) ──────────────────────────

def gerar_hash_placa(placa: str) -> str:
    """Gera o hash criptográfico SHA-256 para anonimização de dados da placa."""
    return hashlib.sha256(placa.strip().upper().encode('utf-8')).hexdigest()

def mascarar_id(uid: str) -> str:
    """Aplica máscara de privacidade corporativa (ex: ABC1D23 -> ABC**23)"""
    uid_clean = uid.strip().upper()
    if len(uid_clean) >= 5:
        return f"{uid_clean[:3]}**{uid_clean[-2:]}"
    return f"{uid_clean}**"

def inicializar_banco():
    """Cria o arquivo físico chargegrid.db e popula tabelas base e usuários de teste."""
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    
    # Tabela de Controle de Acesso Corporativo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            hash_usuario TEXT PRIMARY KEY,
            nome TEXT,
            status TEXT DEFAULT 'ATIVO'
        )
    """)
    
    # Tabela Histórica e Operacional de Sessões em Tempo Real
    # [AJUSTE SPRINT 3]: coluna data_sessao adicionada — sem ela não era
    # possível separar "faturamento de hoje" de "faturamento acumulado".
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_estacao INTEGER,
            usuario TEXT,
            data_sessao TEXT,
            hora_inicio INTEGER,
            kwh_consumidos REAL DEFAULT 0.0,
            valor_sessao REAL DEFAULT 0.0,
            metodo_pagamento TEXT,
            status_pagamento TEXT DEFAULT 'PENDENTE',
            ativa INTEGER DEFAULT 1
        )
    """)
    
    # Usuários Semente (Seeds) para simulação e validação do sistema
    usuarios_teste = [
        (gerar_hash_placa("ABC1D23"), "Cliente Executivo A"),
        (gerar_hash_placa("XYZ9F88"), "Frota Corporativa B"),
        (gerar_hash_placa("GHI3K45"), "Cliente Shopping C"),
        (gerar_hash_placa("DEF7M01"), "Usuário Demo D")
    ]
    cursor.executemany("INSERT OR IGNORE INTO usuarios (hash_usuario, nome) VALUES (?, ?)", usuarios_teste)
    
    conn.commit()
    conn.close()

def validar_usuario(id_usuario: str) -> bool:
    """Camada de Segurança: Valida via Hash se a credencial existe e está ativa."""
    hash_busca = gerar_hash_placa(id_usuario)
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM usuarios WHERE hash_usuario = ?", (hash_busca,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None and resultado[0] == 'ATIVO'

def cadastrar_usuario(placa: str, nome: str = "Usuario Cadastrado") -> bool:
    """
    [AJUSTE SPRINT 3]: Permite registrar uma placa nova autorizada em tempo
    real, sem precisar editar o banco manualmente. Útil pra testar o fluxo
    de autenticação com uma placa diferente das 4 sementes durante a demo
    ou a apresentação final.
    Retorna True se cadastrou um usuário novo, False se já existia.
    """
    hash_novo = gerar_hash_placa(placa)
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO usuarios (hash_usuario, nome) VALUES (?, ?)", (hash_novo, nome))
    conn.commit()
    cadastrou = cursor.rowcount > 0
    conn.close()
    return cadastrou

def criar_pagamento_sandbox(valor: float, id_sessao: Optional[int]) -> dict:
    """
    Gera a cobrança da sessão.
    [AJUSTE SPRINT 3]: por padrão (USAR_API_REAL_MERCADOPAGO=False) monta uma
    simulação local consistente — sem custo, sem internet, sem credencial
    externa. Só tenta a API real do Mercado Pago se a flag estiver ligada
    (e mesmo assim cai no fallback se a chamada falhar).
    Retorna um dicionário {'url': ..., 'transacao_id': ...} — formato estável
    pra quem for consumir isso (CLI hoje, dashboard/totem depois).
    """
    transacao_id = f"SIM-{uuid.uuid4().hex[:10].upper()}"

    if USAR_API_REAL_MERCADOPAGO:
        url = "https://api.mercadopago.com/v1/payments"
        headers = {
            "Authorization": "Bearer TEST-8374928374982374-MOCK-TOKEN",
            "Content-Type": "application/json"
        }
        payload = {
            "transaction_amount": valor,
            "description": f"ChargeGrid CGI - Sessão #{id_sessao}",
            "payment_method_id": "pix",
            "payer": {"email": "motorista@evchallenge.com"}
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=2)
            if response.status_code == 201:
                dados = response.json()
                return {
                    "url": dados.get("point_of_interaction", {}).get("transaction_data", {}).get("ticket_url"),
                    "transacao_id": dados.get("id", transacao_id),
                }
        except Exception:
            pass

    # Simulação local — comportamento padrão do projeto, sem custo nem dependência externa
    return {
        "url": f"https://www.mercadopago.com.br/sandbox/pay?simulation_id={transacao_id}",
        "transacao_id": transacao_id,
    }

def confirmar_pagamento(id_sessao_db: Optional[int]) -> None:
    """
    [AJUSTE SPRINT 3]: Efetiva a baixa financeira no banco (status PAGO,
    sessão inativa). Separado da geração da cobrança de propósito — assim
    outras interfaces (dashboard, totem) podem chamar só essa confirmação
    quando o time construir isso, sem depender do input() de terminal que
    a versão CLI usa.
    """
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sessoes 
        SET status_pagamento = 'PAGO', ativa = 0 
        WHERE id = ?
    """, (id_sessao_db,))
    conn.commit()
    conn.close()


# ─── MÓDULO DE LEITURA — funções prontas para Lucas (chatbot) e Luan (dashboard) ──
# [AJUSTE SPRINT 3]: isso é o que o README pedia e ainda não existia —
# uma função de leitura que Lucas e Luan chamam sem escrever SQL nem
# tocar no motor principal.

def listar_sessoes_ativas() -> list[dict]:
    """Retorna as sessões em andamento agora. Uso: chatbot e dashboard."""
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_estacao, usuario, kwh_consumidos, valor_sessao, metodo_pagamento
        FROM sessoes
        WHERE ativa = 1
    """)
    colunas = ["estacao", "usuario", "kwh", "valor", "pagamento"]
    resultado = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    conn.close()
    return resultado

def obter_status_estacoes() -> dict:
    """
    Retorna o status (Livre/Ocupada) de todas as MAX_ESTACOES estações.
    Resolve a lógica que antes cada consumidor teria que reimplementar:
    o banco só tem linha pra sessão que começou, então "livre" é por
    exclusão — aqui essa exclusão já vem pronta. Uso: dashboard.
    """
    ativas = {s["estacao"] for s in listar_sessoes_ativas()}
    return {
        n: ("Ocupada" if n in ativas else "Livre")
        for n in range(1, MAX_ESTACOES + 1)
    }

def obter_faturamento_dia(data: Optional[str] = None) -> float:
    """
    Soma o valor de sessões PAGAS no dia informado (formato AAAA-MM-DD).
    Sem o parâmetro, usa o dia de hoje. Uso: chatbot ("faturamento de hoje").
    """
    data = data or datetime.date.today().isoformat()
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(valor_sessao), 0)
        FROM sessoes
        WHERE status_pagamento = 'PAGO' AND data_sessao = ?
    """, (data,))
    total = cursor.fetchone()[0]
    conn.close()
    return round(total, 2)

def contar_sessoes_dia(data: Optional[str] = None) -> int:
    """Conta quantas sessões foram iniciadas no dia informado. Uso: chatbot."""
    data = data or datetime.date.today().isoformat()
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sessoes WHERE data_sessao = ?", (data,))
    total = cursor.fetchone()[0]
    conn.close()
    return total


# ─── OCPP 1.6J — Central System simulado ─────────────────────────────────────
def ocpp_enviar(action: str, id_estacao: int, payload: dict) -> None:
    """Simula comunicação com o Central System via OCPP 1.6J."""
    msg = {"action": action, "estacaoId": id_estacao, **payload}
    print(f"[OCPP 1.6J] -> {json.dumps(msg, ensure_ascii=False)}")


# ─── Módulo de IA ─────────────────────────────────────────────────────────────
def ia_prever_demanda(hora: int) -> float:
    """Retorna fator de ocupação previsto para a hora (0.0 a 1.0)."""
    return DEMANDA_PREVISTA_POR_HORA.get(hora, 0.5)

def ia_calcular_tarifa(hora: int, estacoes_ativas: int) -> float:
    """
    Tarifa dinâmica comercial — três camadas:
      1. Horário de pico (12h e 18h–20h): +30%
      2. Alta ocupação (≥3 estações): +15%
      3. IA preditiva — demanda futura alta (≥90%): +20%
    """
    fator = 1.0
    if hora == 12 or 18 <= hora <= 20:
        fator += 0.30
    if estacoes_ativas >= 3:
        fator += 0.15
    demanda = ia_prever_demanda(hora)
    if demanda >= 0.90:
        fator += 0.20
    elif demanda >= 0.75:
        fator += 0.10
    return round(fator, 2)


# ─── DLB — Dynamic Load Balancing ─────────────────────────────────────────────
def contar_ativas() -> int:
    return sum(1 for e in estacoes if e.ativa)

def balancear_carga() -> None:
    """
    Distribui a demanda contratada entre as estações ativas.
    Garante que o limite da concessionária nunca seja ultrapassado.
    """
    n = contar_ativas()
    if n == 0:
        return
    pot = min(LIMITE_POTENCIA_GRID / n, MAX_POTENCIA_ESTACAO)
    print(f"\n[DLB] Redistribuindo carga: {pot:.1f} kW por estação ({n} ativas).")
    for e in estacoes:
        if e.ativa:
            e.potencia_kw = pot


# ─── Simulação de passagem de tempo ───────────────────────────────────────────
def simular_tempo() -> None:
    """Avança +30 min, recalcula consumo e tarifas, emite MeterValues."""
    global consumo_total_diario
    n = contar_ativas()
    if n == 0:
        print("\n[AVISO] Nenhuma sessão comercial ativa.")
        return

    print("\n[SISTEMA] Avançando +30 min...")
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()

    for e in estacoes:
        if not e.ativa:
            continue
        fator              = ia_calcular_tarifa(e.hora_inicio, n)
        energia            = e.potencia_kw * 0.5
        e.kwh_consumidos  += energia
        consumo_total_diario += energia
        e.valor_sessao     = round(e.kwh_consumidos * TARIFA_BASE_KWH * fator, 2)

        # [RAUL]: Sincroniza o consumo acumulado em tempo real no banco sqlite
        cursor.execute("""
            UPDATE sessoes 
            SET kwh_consumidos = ?, valor_sessao = ? 
            WHERE id = ?
        """, (e.kwh_consumidos, e.valor_sessao, e.id_sessao_db))

        ocpp_enviar("MeterValues", e.id_estacao, {
            "usuario":      e.id_usuario,
            "potenciaKw":   round(e.potencia_kw, 2),
            "leituraKwh":   round(e.kwh_consumidos, 2),
            "valorSessao":  e.valor_sessao,
            "fatorTarifa":  fator,
            "iaDemanda":    ia_prever_demanda(e.hora_inicio),
        })

    conn.commit()
    conn.close()


# ─── Início de sessão comercial ───────────────────────────────────────────────
def iniciar_sessao() -> None:
    print(f"\n--- NOVA SESSÃO COMERCIAL ---")
    print(f"Estação (1 a {MAX_ESTACOES}): ", end="")
    try:
        idx = int(input()) - 1
    except ValueError:
        print("[ERRO] Entrada inválida."); return

    if not (0 <= idx < MAX_ESTACOES):
        print("[ERRO] Estação inexistente."); return
    if estacoes[idx].ativa:
        print("[ERRO] Estação ocupada."); return

    print("ID do usuário (digite uma placa cadastrada ex: ABC1D23): ", end="")
    uid = input().strip().upper() or "ANONIMO"

    # [RAUL]: Validação de Segurança Criptográfica obrigatória em ambiente Comercial
    if uid != "ANONIMO" and not validar_usuario(uid):
        print(f"[BLOQUEADO] Usuário com credencial '{uid}' não autorizado no estabelecimento.")
        print("[DICA] Use uma das placas semente (ABC1D23, XYZ9F88, GHI3K45, DEF7M01) ou cadastre uma nova no menu.")
        return

    print("Horário de início (0–23): ", end="")
    try:
        hora = int(input())
        hora = hora if 0 <= hora <= 23 else datetime.datetime.now().hour
    except ValueError:
        hora = datetime.datetime.now().hour

    print("Método de pagamento (PIX / Cartao / App / QRCode): ", end="")
    pagamento = input().strip() or "App"

    # [RAUL]: Aplicação de anonimização visual LGPD antes de persistir/exibir
    uid_mascarado = mascarar_id(uid)
    data_hoje = datetime.date.today().isoformat()

    # [RAUL]: Gravação operacional inicial da sessão no SQLite
    conn = sqlite3.connect("chargegrid.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessoes (id_estacao, usuario, data_sessao, hora_inicio, metodo_pagamento, status_pagamento, ativa)
        VALUES (?, ?, ?, ?, ?, 'PENDENTE', 1)
    """, (idx + 1, uid_mascarado, data_hoje, hora, pagamento))
    id_gerado_db = cursor.lastrowid
    conn.commit()
    conn.close()

    e = estacoes[idx]
    e.id_usuario       = uid_mascarado
    e.hora_inicio      = hora
    e.ativa            = True
    e.metodo_pagamento = pagamento
    e.id_sessao_db     = id_gerado_db  # Aloca a PK recebida do banco

    demanda = ia_prever_demanda(hora)
    fator   = ia_calcular_tarifa(hora, contar_ativas())
    print(f"\n[OK] Sessão iniciada — Estação {idx+1} | ID Registro DB: #{id_gerado_db}")
    print(f"[IA] Demanda prevista para {hora}h: {demanda*100:.0f}% | Tarifa: R$ {TARIFA_BASE_KWH * fator:.2f}/kWh")

    ocpp_enviar("StartTransaction", e.id_estacao, {
        "status":       "Connected",
        "usuario":      uid_mascarado,
        "pagamento":    pagamento,
        "iaDemanda":    demanda,
        "tarifaInicial": round(TARIFA_BASE_KWH * fator, 2),
    })
    balancear_carga()


# ─── Encerramento de sessão + cobrança ────────────────────────────────────────
def encerrar_sessao() -> None:
    global receita_total
    print(f"\n--- ENCERRAR SESSÃO ---")
    print(f"Estação (1 a {MAX_ESTACOES}): ", end="")
    try:
        idx = int(input()) - 1
    except ValueError:
        print("[ERRO] Entrada inválida."); return

    if not (0 <= idx < MAX_ESTACOES) or not estacoes[idx].ativa:
        print("[ERRO] Estação inativa ou inexistente."); return

    e = estacoes[idx]

    # [RAUL]: Dispara processamento financeiro (real ou simulado, conforme USAR_API_REAL_MERCADOPAGO)
    print(f"\n[GATEWAY] Gerando ordem de pagamento no Mercado Pago Sandbox...")
    cobranca = criar_pagamento_sandbox(e.valor_sessao, e.id_sessao_db)

    print(f"\n{'='*54}")
    print(f"   RECIBO DE RECARGA COMERCIAL — ChargeGrid Intelligence")
    print(f"{'='*54}")
    print(f"  Estação:     #{e.id_estacao:02d}")
    print(f"  Usuário:     {e.id_usuario}")
    print(f"  Consumo:     {e.kwh_consumidos:.2f} kWh")
    print(f"  Valor Total: R$ {e.valor_sessao:.2f}")
    print(f"  Pagamento:   {e.metodo_pagamento}")
    print(f"  URL Pix/Checkout Sandbox:")
    print(f"  {cobranca['url']}")
    print(f"  ID da transação: {cobranca['transacao_id']}")
    print(f"{'='*54}")

    # [RAUL]: Confirmação lógica de transação bem sucedida via terminal
    input("\n[MERCADO PAGO] Pressione [ENTER] após o motorista concluir o pagamento...")

    # [AJUSTE SPRINT 3]: confirmação isolada numa função própria — quando o
    # dashboard/totem do Luan existir, ele chama confirmar_pagamento()
    # direto, sem precisar desse input() de terminal.
    confirmar_pagamento(e.id_sessao_db)

    receita_total += e.valor_sessao

    ocpp_enviar("StopTransaction", e.id_estacao, {
        "status":      "Disconnected",
        "usuario":     e.id_usuario,
        "consumoKwh":  round(e.kwh_consumidos, 2),
        "valorFinal":  e.valor_sessao,
        "pagamento":   e.metodo_pagamento,
        "financeiro":  "APROVADO_MERCADOPAGO"
    })
    e.encerrar()
    balancear_carga()


# ─── Painel operacional ───────────────────────────────────────────────────────
def painel_operacional() -> None:
    n = contar_ativas()
    hora_atual = datetime.datetime.now().hour
    demanda_agora = ia_prever_demanda(hora_atual)

    print(f"\n{'='*65}")
    print(f"  ChargeGrid Intelligence — Painel Operacional Comercial")
    print(f"  {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
          f"IA: demanda prevista {demanda_agora*100:.0f}% para {hora_atual}h")
    print(f"{'='*65}")
    print(f"  {'EST':<5} {'STATUS':<8} {'USUÁRIO':<14} {'kW':>6} {'kWh':>8} {'VALOR':>10} {'PAGT':<8}")
    print(f"  {'-'*60}")
    for e in estacoes:
        st = "Ocupada" if e.ativa else "Livre"
        print(f"  {e.id_estacao:02d}    {st:<8} {e.id_usuario:<14} "
              f"{e.potencia_kw:>5.1f}  {e.kwh_consumidos:>7.2f}  "
              f"R$ {e.valor_sessao:>6.2f}  {e.metodo_pagamento:<8}")
    print(f"  {'-'*60}")
    pot_total = sum(e.potencia_kw for e in estacoes if e.ativa)
    print(f"  Ativas: {n}/{MAX_ESTACOES} | "
          f"Potência: {pot_total:.1f}/{LIMITE_POTENCIA_GRID:.0f} kW | "
          f"Consumo dia: {consumo_total_diario:.2f} kWh | "
          f"Receita: R$ {receita_total:.2f}")
    print(f"{'='*65}")


# ─── Cenário de demonstração comercial ───────────────────────────────────────
def demonstracao_comercial() -> None:
    global receita_total, consumo_total_diario

    print("\n╔══════════════════════════════════════════════╗")
    print("║  DEMO — Ambiente Comercial ChargeGrid        ║")
    print("║  Simula estacionamento de shopping center    ║")
    print("╚══════════════════════════════════════════════╝")

    # [RAUL]: Helper adaptado para popular o SQLite também durante a execução da Demo
    def setup(idx, uid, hora, pgto):
        uid_m = mascarar_id(uid)
        data_hoje = datetime.date.today().isoformat()
        conn = sqlite3.connect("chargegrid.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessoes (id_estacao, usuario, data_sessao, hora_inicio, metodo_pagamento, status_pagamento, ativa)
            VALUES (?, ?, ?, ?, ?, 'PENDENTE', 1)
        """, (idx + 1, uid_m, data_hoje, hora, pgto))
        id_db = cursor.lastrowid
        conn.commit()
        conn.close()

        estacoes[idx].id_usuario       = uid_m
        estacoes[idx].hora_inicio      = hora
        estacoes[idx].ativa            = True
        estacoes[idx].metodo_pagamento = pgto
        estacoes[idx].id_sessao_db     = id_db

    print("\n[CENA 1] Cliente 1 conecta (12h — horário de almoço, pico)")
    setup(0, "ABC1D23", 12, "PIX")
    balancear_carga()
    simular_tempo()

    print("\n[CENA 2] DLB entra em ação — mais 2 clientes chegam")
    setup(1, "XYZ9F88", 12, "Cartao")
    setup(2, "GHI3K45", 12, "App")
    balancear_carga()

    print("\n[CENA 3] Horário de pico noturno — cliente 4 conecta às 19h")
    setup(3, "DEF7M01", 19, "QRCode")
    balancear_carga()
    simular_tempo()

    print("\n[CENA 4] Cliente 1 encerra — recibo emitido + DLB redistribui")
    receita_total += estacoes[0].valor_sessao

    # Simula chamada financeira Mercado Pago (real ou simulada, conforme a flag)
    cobranca_demo = criar_pagamento_sandbox(estacoes[0].valor_sessao, estacoes[0].id_sessao_db)

    print(f"\n  RECIBO DEMO: {estacoes[0].id_usuario} | "
          f"{estacoes[0].kwh_consumidos:.2f} kWh | "
          f"R$ {estacoes[0].valor_sessao:.2f} via {estacoes[0].metodo_pagamento}")
    print(f"  [MP SANDBOX LINK]: {cobranca_demo['url']} (transação {cobranca_demo['transacao_id']})")

    confirmar_pagamento(estacoes[0].id_sessao_db)

    ocpp_enviar("StopTransaction", estacoes[0].id_estacao, {
        "usuario": estacoes[0].id_usuario,
        "valorFinal": estacoes[0].valor_sessao,
    })
    estacoes[0].encerrar()
    balancear_carga()

    painel_operacional()

    for i in range(4):
        estacoes[i].encerrar()
    receita_total         = 0.0
    consumo_total_diario  = 0.0
    print("\n--- FIM DA DEMONSTRAÇÃO ---")


# ─── Menu principal ───────────────────────────────────────────────────────────
def main() -> None:
    # [RAUL]: Garante a construção do banco de dados na inicialização do sistema
    inicializar_banco()

    print("\n  ChargeGrid Intelligence — GoodWe Challenge")
    print("  Plataforma de Gestão Comercial de Recarga EV\n")
    demonstracao_comercial()
    while True:
        print("\n══════ ChargeGrid Intelligence — Gestão Comercial ══════")
        print("  1. Iniciar sessão de recarga")
        print("  2. Simular passagem de tempo (+30 min)")
        print("  3. Encerrar sessão e emitir recibo")
        print("  4. Painel operacional")
        print("  5. Rodar demonstração comercial")
        print("  6. Cadastrar novo usuário (placa)")
        print("  7. Ver leitura agregada (uso do chatbot/dashboard)")
        print("  8. Sair")
        print("═══════════════════════════════════════════════════════")
        print("  Escolha: ", end="")
        try:
            op = int(input())
        except ValueError:
            print("[ERRO] Opção inválida."); continue

        if   op == 1: iniciar_sessao()
        elif op == 2: simular_tempo()
        elif op == 3: encerrar_sessao()
        elif op == 4: painel_operacional()
        elif op == 5: demonstracao_comercial()
        elif op == 6:
            print("Placa: ", end="")
            placa_nova = input().strip()
            print("Nome (opcional): ", end="")
            nome_novo = input().strip() or "Usuario Cadastrado"
            if cadastrar_usuario(placa_nova, nome_novo):
                print(f"[OK] Usuário '{placa_nova}' cadastrado e autorizado.")
            else:
                print(f"[INFO] Usuário '{placa_nova}' já estava cadastrado.")
        elif op == 7:
            print(f"\n[LEITURA] Sessões ativas: {listar_sessoes_ativas()}")
            print(f"[LEITURA] Status das estações: {obter_status_estacoes()}")
            print(f"[LEITURA] Faturamento hoje: R$ {obter_faturamento_dia():.2f}")
            print(f"[LEITURA] Sessões hoje: {contar_sessoes_dia()}")
        elif op == 8: print("\n  Sistema encerrado.\n"); break
        else:         print("[ERRO] Opção inválida.")

if __name__ == "__main__":
    main()
