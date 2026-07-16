// ─── Configuração ────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:5000";
const POLL_MS = 3000;

const params = new URLSearchParams(window.location.search);
const ESTACAO = Number(params.get("estacao")) || 1;

document.getElementById("config-hint-n").textContent = ESTACAO;
document.getElementById("station-tag-text").textContent = `Estação ${String(ESTACAO).padStart(2, "0")}`;

// ─── Estado local ─────────────────────────────────────────────────────────────
let metodoSelecionado = "PIX";
let pollTimer = null;
let liveTickTimer = null;
let inicioRealAtual = null;
let telaAtual = "livre";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function irPara(tela) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
  document.getElementById(`screen-${tela}`).classList.add("active");
  telaAtual = tela;

  const tag = document.getElementById("station-tag");
  tag.classList.toggle("ocupada", tela !== "livre");
}

function showToast(msg) {
  const t = document.getElementById("toast-kiosk");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => t.classList.remove("show"), 3200);
}

function fmtMoeda(v) {
  return "R$ " + Number(v).toFixed(2).replace(".", ",");
}

function fmtTempo(segundos) {
  const m = Math.floor(segundos / 60).toString().padStart(2, "0");
  const s = Math.floor(segundos % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

// ─── Seleção de método de pagamento ─────────────────────────────────────────────
document.querySelectorAll(".pagamento-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".pagamento-chip").forEach((c) => c.classList.remove("selecionado"));
    chip.classList.add("selecionado");
    metodoSelecionado = chip.dataset.metodo;
  });
});

// ─── Tela 1 -> 2 ────────────────────────────────────────────────────────────────
document.getElementById("btn-iniciar").addEventListener("click", () => {
  document.getElementById("f-placa").value = "";
  document.getElementById("err-identificacao").textContent = "";
  irPara("identificacao");
  document.getElementById("f-placa").focus();
});

document.getElementById("btn-voltar-1").addEventListener("click", () => irPara("livre"));

// ─── Tela 2 -> 3: confirmar placa e iniciar sessão ──────────────────────────────
document.getElementById("btn-confirmar-placa").addEventListener("click", async () => {
  const placa = document.getElementById("f-placa").value.trim();
  const errEl = document.getElementById("err-identificacao");
  errEl.textContent = "";

  if (!placa) { errEl.textContent = "Digite a placa do veículo."; return; }

  try {
    const res = await fetch(`${API_BASE}/api/sessoes/iniciar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        estacao: ESTACAO,
        usuario: placa,
        hora: new Date().getHours(),
        pagamento: metodoSelecionado,
      }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Não foi possível iniciar a recarga."; return; }

    inicioRealAtual = Date.now();
    iniciarLiveTick();
    irPara("carregando");
    atualizarSessaoAoVivo();
  } catch (err) {
    errEl.textContent = "Sem conexão com o servidor. Chame um atendente.";
  }
});

// ─── Tick do cronômetro visual (a cada 1s, sem depender da API) ────────────────
function iniciarLiveTick() {
  clearInterval(liveTickTimer);
  liveTickTimer = setInterval(() => {
    if (!inicioRealAtual) return;
    const decorridos = (Date.now() - inicioRealAtual) / 1000;
    document.getElementById("live-tempo").textContent = fmtTempo(decorridos);
  }, 1000);
}

// ─── Atualiza kWh/valor/potência lendo o painel (fonte real de verdade) ────────
async function atualizarSessaoAoVivo() {
  try {
    const res = await fetch(`${API_BASE}/api/painel`);
    const painel = await res.json();
    const e = painel.estacoes.find((x) => x.estacao === ESTACAO);
    if (!e) return;

    if (e.status !== "Ocupada" && telaAtual === "carregando") {
      // outra tela/atendente encerrou essa sessão nesse meio tempo
      showToast("Sessão encerrada em outro terminal.");
      resetarParaLivre();
      return;
    }

    if (e.status === "Ocupada") {
      document.getElementById("live-potencia").innerHTML = `${e.potencia_kw.toFixed(1)}<span class="unit">kW</span>`;
      document.getElementById("live-kwh").innerHTML = `${e.kwh_consumidos.toFixed(2)}<span class="unit">kWh</span>`;
      document.getElementById("live-valor").textContent = fmtMoeda(e.valor_sessao);
      if (e.iniciado_em_real) inicioRealAtual = new Date(e.iniciado_em_real).getTime();

      if (telaAtual === "livre") {
        // totem foi recarregado com a sessão já em andamento (ex: outro cliente)
        iniciarLiveTick();
        irPara("carregando");
      }
    } else if (telaAtual !== "livre" && telaAtual !== "pagamento" && telaAtual !== "recibo") {
      irPara("livre");
    }
  } catch (err) {
    // silencioso — o polling tenta de novo no próximo ciclo
  }
}

// ─── Tela 3 -> 4: encerrar sessão e mostrar QR Pix ──────────────────────────────
document.getElementById("btn-encerrar").addEventListener("click", async () => {
  clearInterval(liveTickTimer);
  try {
    const res = await fetch(`${API_BASE}/api/sessoes/${ESTACAO}/encerrar`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) { showToast(data.erro || "Erro ao encerrar."); return; }

    const recibo = data.recibo;
    document.getElementById("valor-cobrado").textContent = fmtMoeda(recibo.valor_sessao);
    document.getElementById("qr-box").innerHTML = "";
    // eslint-disable-next-line no-undef
    new QRCode(document.getElementById("qr-box"), {
      text: recibo.checkout_url,
      width: 200,
      height: 200,
      colorDark: "#0a0e14",
      colorLight: "#ffffff",
    });
    document.getElementById("status-pagamento").innerHTML =
      '<span class="spinner"></span> Aguardando confirmação do Pix...';
    irPara("pagamento");

    // Sandbox: o backend já confirma o pagamento de forma síncrona.
    // Aguardamos alguns segundos só para simular o tempo real de um Pix.
    setTimeout(() => mostrarRecibo(recibo), 3000);
  } catch (err) {
    showToast("Sem conexão com o servidor.");
  }
});

function mostrarRecibo(recibo) {
  const box = document.getElementById("recibo-box");
  box.innerHTML = `
    <div class="recibo-linha"><span class="k">Estação</span><span class="v">#${String(ESTACAO).padStart(2, "0")}</span></div>
    <div class="recibo-linha"><span class="k">Consumo</span><span class="v">${recibo.kwh_consumidos.toFixed(2)} kWh</span></div>
    <div class="recibo-linha"><span class="k">Valor pago</span><span class="v">${fmtMoeda(recibo.valor_sessao)}</span></div>
    <div class="recibo-linha"><span class="k">Método</span><span class="v">${recibo.metodo_pagamento}</span></div>
    <div class="recibo-linha"><span class="k">Transação</span><span class="v">${recibo.transacao_id}</span></div>
  `;
  irPara("recibo");
}

document.getElementById("btn-concluir").addEventListener("click", resetarParaLivre);

function resetarParaLivre() {
  inicioRealAtual = null;
  clearInterval(liveTickTimer);
  irPara("livre");
}

// ─── Polling geral (sincroniza com o backend a cada 3s) ────────────────────────
pollTimer = setInterval(atualizarSessaoAoVivo, POLL_MS);
atualizarSessaoAoVivo();
