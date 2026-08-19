// ─── Configuração ────────────────────────────────────────────────────────────
// file:// ou localhost = ambiente de teste local, aponta pra API local;
// qualquer outro host (site publicado) aponta pra API publicada no Render.
// 127.0.0.1 e não "localhost" de propósito: no Windows, "localhost" resolve
// primeiro pra IPv6 (::1), o servidor Flask escuta em IPv4, e cada chamada
// perde ~1,8s tentando o endereço errado antes de cair no certo — medido.
// Como a tela consulta a API a cada 3s, isso deixava o painel sempre atrasado.
const API_BASE = (location.protocol === "file:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "http://127.0.0.1:5000"
  : "https://chargegrid-api.onrender.com";
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
let modoCadastro = false; // true = placa não reconhecida, esperando nome pra cadastrar

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
  sairDoModoCadastro();
  irPara("identificacao");
  document.getElementById("f-placa").focus();
});

// ─── Cadastro de novo motorista (placa não reconhecida) ─────────────────────
function entrarNoModoCadastro() {
  modoCadastro = true;
  document.getElementById("cadastro-inline").hidden = false;
  document.getElementById("btn-confirmar-placa").textContent = "Cadastrar e continuar";
  document.getElementById("f-nome-novo").focus();
}

function sairDoModoCadastro() {
  modoCadastro = false;
  document.getElementById("cadastro-inline").hidden = true;
  document.getElementById("f-nome-novo").value = "";
  document.getElementById("f-pin-novo").value = "";
  document.getElementById("btn-confirmar-placa").textContent = "Confirmar e carregar";
}

document.getElementById("btn-voltar-1").addEventListener("click", () => {
  sairDoModoCadastro();
  irPara("livre");
});

// ─── Tela 2 -> 3: confirmar placa (ou cadastrar + confirmar) e iniciar sessão ──
document.getElementById("btn-confirmar-placa").addEventListener("click", async () => {
  const placa = document.getElementById("f-placa").value.trim();
  const errEl = document.getElementById("err-identificacao");
  const btn = document.getElementById("btn-confirmar-placa");
  errEl.textContent = "";

  if (!placa) { errEl.textContent = "Digite a placa do veículo."; return; }

  btn.disabled = true;

  try {
    // Placa não reconhecida na tentativa anterior — cadastra antes de continuar.
    if (modoCadastro) {
      const nome = document.getElementById("f-nome-novo").value.trim();
      const pin = document.getElementById("f-pin-novo").value.trim();
      if (!nome) { errEl.textContent = "Digite seu nome pra concluir o cadastro."; return; }
      if (!/^\d{4}$/.test(pin)) { errEl.textContent = "O PIN precisa ter exatamente 4 números."; return; }

      btn.textContent = "Cadastrando...";
      const resCadastro = await fetch(`${API_BASE}/api/usuarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ placa, nome, pin }),
      });
      const dataCadastro = await resCadastro.json();
      if (!resCadastro.ok) { errEl.textContent = dataCadastro.erro || "Não foi possível cadastrar."; return; }
      sairDoModoCadastro();
    }

    btn.textContent = "Confirmando...";
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
    if (!res.ok) {
      if (res.status === 403) {
        errEl.textContent = "Placa não cadastrada ainda.";
        entrarNoModoCadastro();
      } else {
        errEl.textContent = data.erro || "Não foi possível iniciar a recarga.";
      }
      return;
    }

    inicioRealAtual = Date.now();
    iniciarLiveTick();
    irPara("carregando");
    atualizarSessaoAoVivo();
  } catch (err) {
    errEl.textContent = "Sem conexão com o servidor. Chame um atendente.";
  } finally {
    btn.disabled = false;
    btn.textContent = modoCadastro ? "Cadastrar e continuar" : "Confirmar e carregar";
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

// ─── Tarifa atual (mostrada na tela livre, antes do motorista decidir carregar) ─
// Madrugada e janela solar nunca ficam ativas ao mesmo tempo (o motor garante
// isso — geração solar é zero de madrugada), então não precisa decidir qual
// mostrar quando os dois vierem juntos.
function atualizarTarifaNota(painel) {
  const nota = document.getElementById("tarifa-nota");
  if (!nota) return;
  const preco = fmtMoeda(painel.tarifa_kwh_agora);
  if (painel.tarifa_madrugada_ativa) {
    nota.textContent = `Tarifa agora: ${preco}/kWh — desconto de madrugada até ${String(6).padStart(2, "0")}h`;
    nota.classList.add("desconto");
  } else if (painel.tarifa_solar_ativa) {
    nota.textContent = `Tarifa agora: ${preco}/kWh — ☀ desconto de janela solar`;
    nota.classList.add("desconto");
  } else {
    nota.textContent = `Tarifa agora: ${preco}/kWh`;
    nota.classList.remove("desconto");
  }
}

// ─── Atualiza kWh/valor/potência lendo o painel (fonte real de verdade) ────────
async function atualizarSessaoAoVivo() {
  try {
    const res = await fetch(`${API_BASE}/api/painel`);
    const painel = await res.json();
    atualizarTarifaNota(painel);
    const e = painel.estacoes.find((x) => x.estacao === ESTACAO);
    if (!e) return;

    if (e.status !== "Ocupada" && telaAtual === "carregando") {
      // outra tela/atendente encerrou essa sessão nesse meio tempo
      showToast("Sessão encerrada em outro terminal.");
      resetarParaLivre();
      return;
    }

    // Estação em manutenção: bloqueia o fluxo de recarga por completo — não
    // adianta deixar a pessoa digitar a placa pra descobrir só no fim que
    // não dava pra carregar aqui (a API recusaria com 409 de qualquer forma).
    if (e.status === "Manutenção") {
      if (telaAtual === "livre" || telaAtual === "identificacao") {
        document.getElementById("manutencao-motivo-texto").textContent = e.motivo_manutencao
          ? `Motivo: ${e.motivo_manutencao}. Procure outro totem, por favor.`
          : "Esta estação está temporariamente indisponível. Procure outro totem, por favor.";
        irPara("manutencao");
      }
      return;
    }
    if (telaAtual === "manutencao") {
      // saiu da manutenção enquanto a tela esperava — libera o totem de novo
      irPara("livre");
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
    } else if (telaAtual !== "livre" && telaAtual !== "identificacao" && telaAtual !== "pagamento" && telaAtual !== "recibo") {
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
