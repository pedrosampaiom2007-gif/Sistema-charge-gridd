"""
ChargeGrid Intelligence — Plataforma de Gestão Comercial de Recarga EV
GoodWe Challenge

Contexto: ambiente COMERCIAL (shopping, aeroporto, frota corporativa)
  - Múltiplos usuários independentes por sessão
  - Autenticação por placa ou ID de usuário
  - Faturamento individual por sessão
  - Tarifação dinâmica por horário, demanda e congestionamento
  - Dynamic Load Balancing (DLB) automático
  - Protocolo OCPP 1.6J (Central System simulado)
  - Módulo de IA: previsão de demanda e ajuste tarifário inteligente

Diferencial comercial vs residencial/condominial:
  - Residencial: 1 veículo, sem gestão avançada, sem cobrança por usuário
  - Comercial: N usuários simultâneos, billing individual, controle de demanda
    contratada, integração com gateway de pagamento, relatórios operacionais
"""

import json
import datetime
from dataclasses import dataclass
from typing import Optional

# ─── Constantes do sistema ────────────────────────────────────────────────────
MAX_ESTACOES          = 10      # pontos de recarga no estabelecimento comercial
LIMITE_POTENCIA_GRID  = 50.0    # kW — demanda contratada com a concessionária
MAX_POTENCIA_ESTACAO  = 22.0    # kW — limite por carregador AC (Tipo 2)
TARIFA_BASE_KWH       = 0.90    # R$/kWh — tarifa base comercial

# ─── IA: histórico de demanda por hora (padrão de uso comercial) ──────────────
# Representa o padrão aprendido de um estabelecimento comercial real.
# Pico às 12h (almoço), 18h–20h (saída do trabalho), baixo de madrugada.
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
    Cada sessão pertence a um usuário diferente — não a um morador fixo.
    """
    id_estacao:      int
    id_usuario:      str   = "LIVRE"   # placa ou ID do app do motorista
    ativa:           bool  = False
    potencia_kw:     float = 0.0
    kwh_consumidos:  float = 0.0
    hora_inicio:     int   = 0
    valor_sessao:    float = 0.0
    metodo_pagamento: str  = "---"     # PIX, Cartão, App, QR Code

    def encerrar(self):
        self.id_usuario       = "LIVRE"
        self.ativa            = False
        self.potencia_kw      = 0.0
        self.kwh_consumidos   = 0.0
        self.hora_inicio      = 0
        self.valor_sessao     = 0.0
        self.metodo_pagamento = "---"


# ─── Estado do sistema ────────────────────────────────────────────────────────
estacoes: list[SessaoRecarga] = [
    SessaoRecarga(id_estacao=i + 1) for i in range(MAX_ESTACOES)
]
receita_total:         float = 0.0
consumo_total_diario:  float = 0.0


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
    for e in estacoes:
        if not e.ativa:
            continue
        fator              = ia_calcular_tarifa(e.hora_inicio, n)
        energia            = e.potencia_kw * 0.5
        e.kwh_consumidos  += energia
        consumo_total_diario += energia
        e.valor_sessao     = round(e.kwh_consumidos * TARIFA_BASE_KWH * fator, 2)

        ocpp_enviar("MeterValues", e.id_estacao, {
            "usuario":      e.id_usuario,
            "potenciaKw":   round(e.potencia_kw, 2),
            "leituraKwh":   round(e.kwh_consumidos, 2),
            "valorSessao":  e.valor_sessao,
            "fatorTarifa":  fator,
            "iaDemanda":    ia_prever_demanda(e.hora_inicio),
        })


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

    print("ID do usuário (placa ou ID do app): ", end="")
    uid = input().strip()[:12] or "ANONIMO"

    print("Horário de início (0–23): ", end="")
    try:
        hora = int(input())
        hora = hora if 0 <= hora <= 23 else datetime.datetime.now().hour
    except ValueError:
        hora = datetime.datetime.now().hour

    print("Método de pagamento (PIX / Cartao / App / QRCode): ", end="")
    pagamento = input().strip() or "App"

    e = estacoes[idx]
    e.id_usuario       = uid
    e.hora_inicio      = hora
    e.ativa            = True
    e.metodo_pagamento = pagamento

    demanda = ia_prever_demanda(hora)
    fator   = ia_calcular_tarifa(hora, contar_ativas())
    print(f"\n[OK] Sessão iniciada — Estação {idx+1} | Usuário: {uid}")
    print(f"[IA] Demanda prevista para {hora}h: {demanda*100:.0f}% | "
          f"Tarifa estimada: R$ {TARIFA_BASE_KWH * fator:.2f}/kWh")

    ocpp_enviar("StartTransaction", e.id_estacao, {
        "status":       "Connected",
        "usuario":      uid,
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
    receita_total += e.valor_sessao

    print(f"\n{'='*54}")
    print(f"  RECIBO DE RECARGA COMERCIAL — ChargeGrid Intelligence")
    print(f"{'='*54}")
    print(f"  Estação:    #{e.id_estacao:02d}")
    print(f"  Usuário:    {e.id_usuario}")
    print(f"  Consumo:    {e.kwh_consumidos:.2f} kWh")
    print(f"  Valor:      R$ {e.valor_sessao:.2f}")
    print(f"  Pagamento:  {e.metodo_pagamento}")
    print(f"{'='*54}")

    ocpp_enviar("StopTransaction", e.id_estacao, {
        "status":      "Disconnected",
        "usuario":     e.id_usuario,
        "consumoKwh":  round(e.kwh_consumidos, 2),
        "valorFinal":  e.valor_sessao,
        "pagamento":   e.metodo_pagamento,
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

    def setup(idx, uid, hora, pgto):
        estacoes[idx].id_usuario       = uid
        estacoes[idx].hora_inicio      = hora
        estacoes[idx].ativa            = True
        estacoes[idx].metodo_pagamento = pgto

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
    print(f"\n  RECIBO: {estacoes[0].id_usuario} | "
          f"{estacoes[0].kwh_consumidos:.2f} kWh | "
          f"R$ {estacoes[0].valor_sessao:.2f} via {estacoes[0].metodo_pagamento}")
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
        print("  6. Sair")
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
        elif op == 6: print("\n  Sistema encerrado.\n"); break
        else:         print("[ERRO] Opção inválida.")

if __name__ == "__main__":
    main()
