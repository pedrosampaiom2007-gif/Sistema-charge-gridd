// ─── Configuração ────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:5000";
const POLL_MS = 4000;
const MAX_POTENCIA_ESTACAO = 22.0; // espelha MAX_POTENCIA_ESTACAO do backend

document.getElementById("api-base-label").textContent = API_BASE;

// ─── Estado local ─────────────────────────────────────────────────────────────
let estacaoSelecionada = null;
let pollTimer = null;

// ─── Autenticação de administrador ─────────────────────────────────────────────
// /api/painel fica sem login (o totem também precisa dele) — só /api/kpis e
// /api/demanda-ia (dado agregado: faturamento total, curva de demanda) exigem
// token. Token guardado em sessionStorage: some ao fechar a aba, não é
// persistente entre sessões — coerente com o token em si só viver enquanto o
// processo da API estiver de pé.
const TOKEN_KEY = "cg_admin_token";
let adminToken = sessionStorage.getItem(TOKEN_KEY);

function iniciarApp() {
  document.getElementById("overlay-login").classList.remove("open");
  refresh();
  pollTimer = setInterval(refresh, POLL_MS);
}

async function fazerLogin() {
  const usuario = document.getElementById("f-admin-usuario").value.trim();
  const senha = document.getElementById("f-admin-senha").value;
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";

  if (!usuario || !senha) { errEl.textContent = "Informe usuário e senha."; return; }

  try {
    const res = await fetch(`${API_BASE}/api/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario, senha }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Falha no login."; return; }
    adminToken = data.token;
    sessionStorage.setItem(TOKEN_KEY, adminToken);
    iniciarApp();
  } catch (err) {
    errEl.textContent = "Erro de conexão com a API.";
  }
}

// ─── Helpers de UI ────────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => t.classList.remove("show"), 3200);
}

function fmtMoeda(v) {
  return "R$ " + Number(v).toFixed(2).replace(".", ",");
}

// ─── Gauge (dial de potência) ─────────────────────────────────────────────────
// Semi-círculo de 180°, agulha aponta a potência atual da estação (0–22kW).
function gaugeSVG(kw, ativa) {
  const w = 150, h = 84, cx = 75, cy = 78, r = 60;
  const frac = Math.max(0, Math.min(1, kw / MAX_POTENCIA_ESTACAO));
  const angle = Math.PI * (1 - frac); // 180deg (esquerda) -> 0deg (direita)
  const needleX = cx + r * 0.82 * Math.cos(angle);
  const needleY = cy - r * 0.82 * Math.sin(angle);
  const color = ativa ? "var(--amber)" : "var(--muted-dim)";

  const arcSegs = 5;
  let ticks = "";
  for (let i = 0; i <= arcSegs; i++) {
    const a = Math.PI * (1 - i / arcSegs);
    const x1 = cx + (r + 4) * Math.cos(a);
    const y1 = cy - (r + 4) * Math.sin(a);
    const x2 = cx + (r - 4) * Math.cos(a);
    const y2 = cy - (r - 4) * Math.sin(a);
    ticks += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--line-bright)" stroke-width="2"/>`;
  }

  const arcLen = Math.PI * r;
  return `
  <svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}"
          fill="none" stroke="var(--line-bright)" stroke-width="8" stroke-linecap="round"/>
    <path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}"
          fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"
          stroke-dasharray="${arcLen}"
          stroke-dashoffset="${arcLen * (1 - frac)}"/>
    ${ticks}
    <line x1="${cx}" y1="${cy}" x2="${needleX}" y2="${needleY}" stroke="${color}" stroke-width="3" stroke-linecap="round"/>
    <circle cx="${cx}" cy="${cy}" r="5" fill="${color}"/>
    <text x="${cx}" y="${cy - 14}" text-anchor="middle" fill="var(--ink)" font-family="IBM Plex Mono, monospace" font-size="16" font-weight="500">${kw.toFixed(1)}</text>
    <text x="${cx}" y="${cy - 1}" text-anchor="middle" fill="var(--muted)" font-family="IBM Plex Mono, monospace" font-size="9">kW</text>
  </svg>`;
}

// ─── Render: estações ──────────────────────────────────────────────────────────
function renderEstacoes(estacoes) {
  const grid = document.getElementById("station-grid");
  grid.innerHTML = "";

  estacoes.forEach((e) => {
    const ativa = e.status === "Ocupada";
    const card = document.createElement("div");
    card.className = `station ${ativa ? "ocupada" : "livre"}`;
    card.innerHTML = `
      <div class="head">
        <span class="id">EST-${String(e.estacao).padStart(2, "0")}</span>
        <span class="pill ${ativa ? "ocupada" : "livre"}">${ativa ? "Ocupada" : "Livre"}</span>
      </div>
      <div class="gauge-wrap">${gaugeSVG(e.potencia_kw, ativa)}</div>
      <div class="usuario">${ativa ? e.usuario : "—"}</div>
      <div class="station-stats">
        <div><div class="k">kWh</div><div class="v">${e.kwh_consumidos.toFixed(2)}</div></div>
        <div><div class="k">Valor</div><div class="v">${fmtMoeda(e.valor_sessao)}</div></div>
        <div><div class="k">Início</div><div class="v">${ativa ? e.hora_inicio + "h" : "--"}</div></div>
        <div><div class="k">Pagto</div><div class="v">${e.metodo_pagamento}</div></div>
      </div>
      <div class="actions">
        <button class="btn small ${ativa ? "danger" : ""}" data-estacao="${e.estacao}" data-ativa="${ativa}">
          ${ativa ? "Encerrar sessão" : "Iniciar sessão"}
        </button>
      </div>
    `;
    grid.appendChild(card);
  });

  grid.querySelectorAll("button[data-estacao]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const num = Number(btn.dataset.estacao);
      const ativa = btn.dataset.ativa === "true";
      ativa ? encerrarSessao(num) : abrirModal(num);
    });
  });
}

// ─── Render: gráfico de demanda ────────────────────────────────────────────────
function renderDemandChart(curva, horaAtual) {
  const svg = document.getElementById("demand-chart");
  const W = 720, H = 180, padL = 30, padB = 22, padT = 12, padR = 10;
  const plotW = W - padL - padR, plotH = H - padT - padB;

  const pts = curva.map((c, i) => {
    const x = padL + (i / (curva.length - 1)) * plotW;
    const y = padT + (1 - c.demanda) * plotH;
    return [x, y];
  });

  const path = pts.map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`)).join(" ");
  const areaPath = `${path} L ${pts[pts.length - 1][0]} ${padT + plotH} L ${pts[0][0]} ${padT + plotH} Z`;

  let gridLines = "";
  for (let g = 0; g <= 4; g++) {
    const y = padT + (g / 4) * plotH;
    gridLines += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="var(--line)" stroke-width="1"/>`;
  }

  let hourLabels = "";
  [0, 6, 12, 18, 23].forEach((h) => {
    const x = padL + (h / (curva.length - 1)) * plotW;
    hourLabels += `<text x="${x}" y="${H - 4}" fill="var(--muted-dim)" font-family="IBM Plex Mono, monospace" font-size="10" text-anchor="middle">${h}h</text>`;
  });

  const nowX = padL + (horaAtual / (curva.length - 1)) * plotW;

  // Marcador de pico previsto pela IA (requisito: "gráficos com a previsão de pico")
  const pico = curva.reduce((max, c) => (c.demanda > max.demanda ? c : max), curva[0]);
  const picoX = padL + (pico.hora / (curva.length - 1)) * plotW;
  const picoY = padT + (1 - pico.demanda) * plotH;
  const labelAcima = picoY > padT + 24; // evita label cortada no topo do gráfico

  svg.innerHTML = `
    ${gridLines}
    <path d="${areaPath}" fill="var(--amber)" opacity="0.08"/>
    <path d="${path}" fill="none" stroke="var(--amber)" stroke-width="2"/>
    <line x1="${nowX}" y1="${padT}" x2="${nowX}" y2="${padT + plotH}" stroke="var(--cyan)" stroke-width="1" stroke-dasharray="3 3"/>
    <circle cx="${nowX}" cy="${padT + (1 - (curva[horaAtual] ? curva[horaAtual].demanda : 0)) * plotH}" r="4" fill="var(--cyan)"/>
    <circle cx="${picoX}" cy="${picoY}" r="5" fill="var(--void)" stroke="var(--amber)" stroke-width="2"/>
    <text x="${picoX}" y="${labelAcima ? picoY - 12 : picoY + 20}" text-anchor="middle"
          fill="var(--amber)" font-family="IBM Plex Mono, monospace" font-size="11" font-weight="500">
      Pico ${pico.hora}h · ${Math.round(pico.demanda * 100)}%
    </text>
    ${hourLabels}
  `;
}

// ─── Fetch + refresh geral ──────────────────────────────────────────────────────
async function refresh() {
  try {
    const authHeaders = { "Authorization": `Bearer ${adminToken}` };
    const [painelRes, kpisRes] = await Promise.all([
      fetch(`${API_BASE}/api/painel`),
      fetch(`${API_BASE}/api/kpis`, { headers: authHeaders }),
    ]);

    if (kpisRes.status === 401) {
      clearInterval(pollTimer);
      sessionStorage.removeItem(TOKEN_KEY);
      adminToken = null;
      document.getElementById("overlay-login").classList.add("open");
      showToast("Sessão expirada — faça login novamente.");
      return;
    }
    if (!painelRes.ok || !kpisRes.ok) throw new Error("Falha na resposta da API");
    const painel = await painelRes.json();
    const kpis = await kpisRes.json();

    document.getElementById("ro-hora").textContent =
      new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    document.getElementById("ro-demanda").textContent = `${Math.round(painel.demanda_ia_agora * 100)}%`;
    document.getElementById("ro-potencia").textContent =
      `${painel.potencia_usada_kw.toFixed(1)} / ${painel.limite_potencia_grid_kw.toFixed(0)} kW`;
    document.getElementById("ro-potencia-bar").style.width =
      `${Math.min(100, (painel.potencia_usada_kw / painel.limite_potencia_grid_kw) * 100)}%`;

    document.getElementById("kpi-faturamento").innerHTML =
      `${fmtMoeda(kpis.faturamento_dia)}`;
    document.getElementById("kpi-sessoes").textContent = kpis.sessoes_dia;
    document.getElementById("kpi-ativas").innerHTML = `${painel.ativas}<span class="unit">/ ${painel.max_estacoes}</span>`;
    document.getElementById("kpi-consumo").innerHTML =
      `${painel.consumo_total_diario_kwh.toFixed(1)}<span class="unit">kWh</span>`;

    renderEstacoes(painel.estacoes);

    const curvaRes = await fetch(`${API_BASE}/api/demanda-ia`, { headers: authHeaders });
    const curva = await curvaRes.json();
    renderDemandChart(curva, painel.hora_atual);
  } catch (err) {
    showToast("Não foi possível falar com a API. Ela está rodando em " + API_BASE + "?");
    console.error(err);
  }
}

// ─── Modal: iniciar sessão ──────────────────────────────────────────────────────
function abrirModal(numEstacao) {
  estacaoSelecionada = numEstacao;
  document.getElementById("modal-title").textContent = `Iniciar sessão — Estação ${numEstacao}`;
  document.getElementById("f-placa").value = "";
  document.getElementById("f-hora").value = new Date().getHours();
  document.getElementById("modal-error").textContent = "";
  document.getElementById("overlay").classList.add("open");
  document.getElementById("f-placa").focus();
}

function fecharModal() {
  document.getElementById("overlay").classList.remove("open");
  estacaoSelecionada = null;
}

async function confirmarInicio() {
  const placa = document.getElementById("f-placa").value.trim();
  const hora = document.getElementById("f-hora").value;
  const pagamento = document.getElementById("f-pagamento").value;
  const errEl = document.getElementById("modal-error");
  errEl.textContent = "";

  if (!placa) { errEl.textContent = "Informe a placa do usuário."; return; }

  try {
    const res = await fetch(`${API_BASE}/api/sessoes/iniciar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estacao: estacaoSelecionada, usuario: placa, hora, pagamento }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Erro ao iniciar sessão."; return; }
    showToast(`Sessão iniciada na estação ${estacaoSelecionada}.`);
    fecharModal();
    refresh();
  } catch (err) {
    errEl.textContent = "Erro de conexão com a API.";
  }
}

async function encerrarSessao(numEstacao) {
  try {
    const res = await fetch(`${API_BASE}/api/sessoes/${numEstacao}/encerrar`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) { showToast(data.erro || "Erro ao encerrar sessão."); return; }
    showToast(`Recibo emitido — Estação ${numEstacao}: ${fmtMoeda(data.recibo.valor_sessao)}`);
    refresh();
  } catch (err) {
    showToast("Erro de conexão com a API.");
  }
}

// ─── Listeners globais ──────────────────────────────────────────────────────────
document.getElementById("btn-refresh").addEventListener("click", refresh);
document.getElementById("btn-cancel").addEventListener("click", fecharModal);
document.getElementById("btn-confirm").addEventListener("click", confirmarInicio);
document.getElementById("overlay").addEventListener("click", (e) => {
  if (e.target.id === "overlay") fecharModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") fecharModal();
});
document.getElementById("btn-login").addEventListener("click", fazerLogin);
document.getElementById("f-admin-senha").addEventListener("keydown", (e) => {
  if (e.key === "Enter") fazerLogin();
});

// ─── Início ──────────────────────────────────────────────────────────────────────
if (adminToken) {
  iniciarApp();
} else {
  document.getElementById("f-admin-usuario").focus();
}
