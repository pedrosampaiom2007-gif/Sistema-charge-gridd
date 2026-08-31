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
const POLL_MS = 4000;
const MAX_POTENCIA_ESTACAO = 22.0; // espelha MAX_POTENCIA_ESTACAO do backend

document.getElementById("api-base-label").textContent = API_BASE;

// ─── Estado local ─────────────────────────────────────────────────────────────
let estacaoSelecionada = null;
let estacaoParaManutencao = null;
let pollTimer = null;
// Guardam a curva mais recente de cada gráfico pro tooltip ler sem precisar
// de uma nova requisição — atualizadas a cada render, lidas a cada hover.
let _curvaDemandaAtual = [];
let _curvaSolarAtual = [];

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

async function logoutAdmin() {
  if (adminToken) {
    try {
      await fetch(`${API_BASE}/api/admin/logout`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${adminToken}` },
      });
    } catch (err) {
      // segue o logout local mesmo se a API não responder — não trava o usuário
    }
  }
  clearInterval(pollTimer);
  sessionStorage.removeItem(TOKEN_KEY);
  adminToken = null;
  document.getElementById("overlay-login").classList.add("open");
}

async function fazerLogin() {
  const usuario = document.getElementById("f-admin-usuario").value.trim();
  const senha = document.getElementById("f-admin-senha").value;
  const errEl = document.getElementById("login-error");
  const btn = document.getElementById("btn-login");
  errEl.textContent = "";

  if (!usuario || !senha) { errEl.textContent = "Informe usuário e senha."; return; }

  const textoOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Entrando...";

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
  } finally {
    btn.disabled = false;
    btn.textContent = textoOriginal;
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
// status pode ser "Ocupada", "Livre" ou "Manutenção" (terceiro estado — tira
// o carregador de circulação sem apagar ele do sistema, ex: cabo com defeito).
function classeDoStatus(status) {
  if (status === "Ocupada") return "ocupada";
  if (status === "Manutenção") return "manutencao";
  return "livre";
}

// Resultado do simulador por estação — guardado FORA do render, porque
// renderEstacoes() reconstrói o grid inteiro a cada poll (4s); sem isso, o
// resultado sumia antes do admin ter tempo de ler. Some quando a estação
// deixa de estar ativa (sessão encerrada), pra não mostrar prévia velha
// pro próximo cliente que ligar naquela estação.
const simulacoesEstacao = {}; // { [estacao]: "texto pronto pra mostrar" }

function renderEstacoes(estacoes) {
  const grid = document.getElementById("station-grid");
  grid.innerHTML = "";

  estacoes.forEach((e) => {
    const ativa = e.status === "Ocupada";
    const emManutencao = e.status === "Manutenção";
    const classe = classeDoStatus(e.status);

    if (!ativa) delete simulacoesEstacao[e.estacao];

    // O botão principal muda de ação conforme o estado; "colocar em
    // manutenção" só faz sentido pra estação Livre — não dá pra marcar uma
    // Ocupada (a API recusa, ver aplicar_manutencao no motor) nem faz
    // sentido oferecer de novo numa que já está em manutenção.
    let botaoPrincipal;
    let botaoSimular = "";
    if (ativa) {
      botaoPrincipal = `<button class="btn small danger" data-estacao="${e.estacao}" data-acao="encerrar">Encerrar sessão</button>`;
      botaoSimular = `<button class="btn small" data-estacao="${e.estacao}" data-acao="simular">Simular +30min</button>`;
    } else if (emManutencao) {
      botaoPrincipal = `<button class="btn small" data-estacao="${e.estacao}" data-acao="sair-manutencao">Sair da manutenção</button>`;
    } else {
      botaoPrincipal = `<button class="btn small" data-estacao="${e.estacao}" data-acao="iniciar">Iniciar sessão</button>`;
    }
    const linkManutencao = (!ativa && !emManutencao)
      ? `<button class="link-manutencao" data-estacao="${e.estacao}" data-acao="entrar-manutencao">Colocar em manutenção</button>`
      : "";
    const motivo = (emManutencao && e.motivo_manutencao)
      ? `<div class="motivo-manutencao">Motivo: ${e.motivo_manutencao}</div>`
      : "";
    const simTexto = simulacoesEstacao[e.estacao];

    const card = document.createElement("div");
    card.className = `station ${classe}`;
    card.innerHTML = `
      <div class="head">
        <span class="id">EST-${String(e.estacao).padStart(2, "0")}</span>
        <span class="pill ${classe}">${e.status}</span>
      </div>
      <div class="gauge-wrap">${gaugeSVG(e.potencia_kw, ativa)}</div>
      <div class="usuario">${ativa ? e.usuario : "—"}</div>
      <div class="station-stats">
        <div><div class="k">kWh</div><div class="v">${e.kwh_consumidos.toFixed(2)}</div></div>
        <div><div class="k">Valor</div><div class="v">${fmtMoeda(e.valor_sessao)}</div></div>
        <div><div class="k">Início</div><div class="v">${ativa ? e.hora_inicio + "h" : "--"}</div></div>
        <div><div class="k">Pagto</div><div class="v">${e.metodo_pagamento}</div></div>
      </div>
      ${motivo}
      <div class="actions">${botaoPrincipal}${botaoSimular}</div>
      <div class="simulador-resultado-admin" id="sim-resultado-${e.estacao}" ${simTexto ? "" : "hidden"}>${simTexto || ""}</div>
      ${linkManutencao}
    `;
    grid.appendChild(card);
  });

  grid.querySelectorAll("button[data-estacao]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const num = Number(btn.dataset.estacao);
      const acao = btn.dataset.acao;
      if (acao === "encerrar") encerrarSessao(num);
      else if (acao === "iniciar") abrirModal(num);
      else if (acao === "entrar-manutencao") abrirModalManutencao(num);
      else if (acao === "sair-manutencao") sairDaManutencao(num);
      else if (acao === "simular") simularTempoEstacao(num);
    });
  });
}

// ─── Rótulos de hora no eixo X (0h, 6h, 12h, 18h, 23h) ─────────────────────────
// text-anchor="middle" nas pontas (0h e 23h) fazia metade do texto vazar pra
// fora da área do gráfico — em x=0 (padL) sobra pouca margem à esquerda, e em
// x=plotW (W-padR) sobra só 10px à direita, menos que a metade da largura de
// "23h". A correção: ancorar pelo início/fim nas pontas, não pelo centro —
// aí o texto cresce PRA DENTRO da área do gráfico em vez de pros dois lados.
function hourLabelsSVG(horas, calcularX, H) {
  return horas.map((h, i) => {
    const anchor = i === 0 ? "start" : i === horas.length - 1 ? "end" : "middle";
    return `<text x="${calcularX(h)}" y="${H - 4}" fill="var(--muted-dim)" font-family="IBM Plex Mono, monospace" font-size="10" text-anchor="${anchor}">${h}h</text>`;
  }).join("");
}

// ─── Tooltip interativo (hover mostra hora + valor exato) ──────────────────────
// Um listener por gráfico, montado uma vez só — em vez de recriar a cada
// render (o poll roda a cada 4s, e isso vazaria um listener novo por poll).
// A curva usada no hover vem de uma variável atualizada a cada render, não de
// uma nova chamada à API — não faz sentido buscar dado de novo só pra mostrar
// o que já está na tela.
function configurarTooltipGrafico(svgId, obterCurva, formatar) {
  const svg = document.getElementById(svgId);
  const tooltip = document.getElementById("chart-tooltip");
  const W = 720, padL = 30, padR = 10, plotW = W - padL - padR;

  svg.addEventListener("mousemove", (e) => {
    const curva = obterCurva();
    if (!curva.length) return;
    const rect = svg.getBoundingClientRect();
    const xSvg = (e.clientX - rect.left) * (W / rect.width);
    const horaFloat = ((xSvg - padL) / plotW) * (curva.length - 1);
    const hora = Math.max(0, Math.min(curva.length - 1, Math.round(horaFloat)));
    const ponto = curva[hora];
    if (!ponto) return;

    tooltip.innerHTML = formatar(hora, ponto);
    tooltip.style.left = `${e.clientX + 14}px`;
    tooltip.style.top = `${e.clientY - 12}px`;
    tooltip.classList.add("show");
  });

  svg.addEventListener("mouseleave", () => tooltip.classList.remove("show"));
}

// ─── Render: gráfico de demanda ────────────────────────────────────────────────
function renderDemandChart(curva, horaAtual) {
  _curvaDemandaAtual = curva;
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

  const hourLabels = hourLabelsSVG([0, 6, 12, 18, 23], (h) => padL + (h / (curva.length - 1)) * plotW, H);

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

// ─── Render: gráfico de geração solar prevista ──────────────────────────────────
// Mesmo layout do gráfico de demanda, mas com cor invertida (ciano pra curva,
// âmbar pro marcador de "agora") pra ficar visualmente distinto sem inventar
// uma terceira paleta — e uma faixa sombreada marcando a janela de desconto
// solar, que muda de hora conforme a previsão do dia (não é um horário fixo).
function renderSolarChart(curva, horaAtual, fonte) {
  _curvaSolarAtual = curva;
  const svg = document.getElementById("solar-chart");
  const W = 720, H = 180, padL = 30, padB = 22, padT = 12, padR = 10;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const passo = plotW / (curva.length - 1);

  const pts = curva.map((c, i) => [padL + i * passo, padT + (1 - c.geracao_relativa) * plotH]);
  const path = pts.map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`)).join(" ");
  const areaPath = `${path} L ${pts[pts.length - 1][0]} ${padT + plotH} L ${pts[0][0]} ${padT + plotH} Z`;

  let gridLines = "";
  for (let g = 0; g <= 4; g++) {
    const y = padT + (g / 4) * plotH;
    gridLines += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="var(--line)" stroke-width="1"/>`;
  }

  const hourLabels = hourLabelsSVG([0, 6, 12, 18, 23], (h) => padL + h * passo, H);

  // Faixa da janela solar: pode ser descontínua (nuvem passageira desloca a
  // previsão), então desenha um retângulo por hora marcada em vez de assumir
  // um intervalo contínuo.
  let faixaJanela = "";
  curva.forEach((c, i) => {
    if (c.janela_solar) {
      faixaJanela += `<rect x="${padL + i * passo - passo / 2}" y="${padT}" width="${passo}" height="${plotH}" fill="var(--cyan)" opacity="0.07"/>`;
    }
  });

  const nowX = padL + horaAtual * passo;
  const geracaoAgora = curva[horaAtual] ? curva[horaAtual].geracao_relativa : 0;

  svg.innerHTML = `
    ${gridLines}
    ${faixaJanela}
    <path d="${areaPath}" fill="var(--cyan)" opacity="0.10"/>
    <path d="${path}" fill="none" stroke="var(--cyan)" stroke-width="2"/>
    <line x1="${nowX}" y1="${padT}" x2="${nowX}" y2="${padT + plotH}" stroke="var(--amber)" stroke-width="1" stroke-dasharray="3 3"/>
    <circle cx="${nowX}" cy="${padT + (1 - geracaoAgora) * plotH}" r="4" fill="var(--amber)"/>
    ${hourLabels}
  `;

  document.getElementById("solar-fonte").textContent =
    fonte === "open-meteo" ? "previsão real (Open-Meteo)" : "perfil padrão (previsão indisponível)";
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
    // consumo do dia vem do /api/kpis (logado), não do /api/painel (aberto):
    // é número agregado do negócio, e o painel é a rota que o totem usa.
    document.getElementById("kpi-consumo").innerHTML =
      `${kpis.consumo_total_diario_kwh.toFixed(1)}<span class="unit">kWh</span>`;

    const roTarifa = document.getElementById("ro-tarifa");
    roTarifa.textContent = `${fmtMoeda(painel.tarifa_kwh_agora)}/kWh`;
    const temDesconto = painel.tarifa_madrugada_ativa || painel.tarifa_solar_ativa;
    // amber só no horário de ponta real (a energia está de fato mais cara);
    // fora disso, cyan quando há desconto, cor neutra no resto do dia — antes
    // qualquer hora sem desconto virava amber, mesmo sem ser pico de verdade.
    roTarifa.className = `value ${temDesconto ? "cyan" : painel.tarifa_pico_ativa ? "amber" : ""}`;
    roTarifa.title = painel.tarifa_madrugada_ativa
      ? "Desconto de madrugada ativo (0h-6h)"
      : painel.tarifa_solar_ativa
      ? "Desconto da janela solar ativo — horário de maior geração fotovoltaica prevista"
      : painel.tarifa_pico_ativa
      ? "Horário de ponta da rede (18h-21h) — tarifa mais cara"
      : "";

    renderEstacoes(painel.estacoes);

    const [curvaRes, solarRes] = await Promise.all([
      fetch(`${API_BASE}/api/demanda-ia`, { headers: authHeaders }),
      fetch(`${API_BASE}/api/solar`),
    ]);
    const curva = await curvaRes.json();
    renderDemandChart(curva, painel.hora_atual);

    const solarDados = await solarRes.json();
    renderSolarChart(solarDados.curva, painel.hora_atual, solarDados.fonte);
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

// ─── Simulador "e se essa sessão continuasse por mais 30 min?" ─────────────
// Mesma rota que o totem usa (api_estimar_sessao) — não recalcula tarifa
// aqui, só mostra o que a API já calculou, pra nunca divergir do valor que
// seria cobrado de verdade. Resultado fica em simulacoesEstacao (ver
// comentário lá em cima) pra sobreviver ao próximo poll.
async function simularTempoEstacao(numEstacao) {
  try {
    const res = await fetch(`${API_BASE}/api/sessoes/${numEstacao}/estimar?minutos=30`);
    const data = await res.json();
    if (!res.ok) { showToast(data.erro || "Não foi possível simular agora."); return; }

    simulacoesEstacao[numEstacao] =
      `+30min ≈ <b>${fmtMoeda(data.valor_projetado)}</b> (+${fmtMoeda(data.custo_adicional)})`;

    const el = document.getElementById(`sim-resultado-${numEstacao}`);
    if (el) { el.innerHTML = simulacoesEstacao[numEstacao]; el.hidden = false; }
  } catch (err) {
    showToast("Erro de conexão com a API.");
  }
}

// ─── Modal: colocar estação em manutenção ───────────────────────────────────
function abrirModalManutencao(numEstacao) {
  estacaoParaManutencao = numEstacao;
  document.getElementById("manutencao-title").textContent = `Colocar em manutenção — Estação ${numEstacao}`;
  document.getElementById("f-motivo-manutencao").value = "";
  document.getElementById("manutencao-error").textContent = "";
  document.getElementById("overlay-manutencao").classList.add("open");
  document.getElementById("f-motivo-manutencao").focus();
}

function fecharModalManutencao() {
  document.getElementById("overlay-manutencao").classList.remove("open");
  estacaoParaManutencao = null;
}

async function confirmarManutencao() {
  const motivo = document.getElementById("f-motivo-manutencao").value.trim();
  const errEl = document.getElementById("manutencao-error");
  errEl.textContent = "";

  try {
    const res = await fetch(`${API_BASE}/api/estacoes/${estacaoParaManutencao}/manutencao`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${adminToken}` },
      body: JSON.stringify({ motivo }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Não foi possível colocar em manutenção."; return; }
    showToast(`Estação ${estacaoParaManutencao} em manutenção.`);
    fecharModalManutencao();
    refresh();
  } catch (err) {
    errEl.textContent = "Erro de conexão com a API.";
  }
}

async function sairDaManutencao(numEstacao) {
  try {
    const res = await fetch(`${API_BASE}/api/estacoes/${numEstacao}/manutencao/encerrar`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${adminToken}` },
    });
    if (!res.ok) { showToast("Erro ao tirar da manutenção."); return; }
    showToast(`Estação ${numEstacao} de volta ao normal.`);
    refresh();
  } catch (err) {
    showToast("Erro de conexão com a API.");
  }
}

// ─── Relatório do dia ────────────────────────────────────────────────────────
// Baixa via fetch (não um <a href> direto) porque precisa mandar o header de
// autorização — a rota é admin-only, igual /api/kpis.
async function baixarRelatorio() {
  try {
    const res = await fetch(`${API_BASE}/api/relatorio`, {
      headers: { "Authorization": `Bearer ${adminToken}` },
    });
    if (!res.ok) { showToast("Não foi possível gerar o relatório."); return; }

    const disposicao = res.headers.get("Content-Disposition") || "";
    const nomeMatch = disposicao.match(/filename="?([^"]+)"?/);
    const nomeArquivo = nomeMatch ? nomeMatch[1] : "relatorio_chargegrid.txt";

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = nomeArquivo;
    link.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast("Erro de conexão com a API.");
  }
}

// ─── Assistente IA (painel lateral) ────────────────────────────────────────────
function abrirPainelIA() {
  if (!adminToken) { showToast("Faça login para usar o assistente."); return; }
  document.getElementById("ia-panel").classList.add("open");
  document.getElementById("ia-panel-backdrop").classList.add("open");
  document.getElementById("ia-panel").setAttribute("aria-hidden", "false");
  document.getElementById("ia-chat-input").focus();
}

function fecharPainelIA() {
  document.getElementById("ia-panel").classList.remove("open");
  document.getElementById("ia-panel-backdrop").classList.remove("open");
  document.getElementById("ia-panel").setAttribute("aria-hidden", "true");
}

// Escapa HTML antes de qualquer coisa: o texto vem de um modelo de IA, nunca
// deve virar HTML/script executável no navegador de quem só está perguntando
// sobre faturamento ou disponibilidade de estação.
function escaparHTML(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

// Markdown básico (negrito, itálico, código inline, listas) — o Groq
// devolve as respostas formatadas assim, e sem isso o balão do chat mostrava
// os asteriscos/traços literais em vez do texto formatado.
function renderizarMarkdown(texto) {
  let html = escaparHTML(texto);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])/g, "<em>$1</em>");

  // Agrupa linhas "- item" / "1. item" consecutivas num <ul>/<ol>; o resto
  // vira parágrafo, pra respeitar as quebras de linha que o modelo manda.
  const saida = [];
  let listaAtual = null;
  for (const linha of html.split("\n")) {
    const itemUl = linha.match(/^[-*]\s+(.+)/);
    const itemOl = linha.match(/^\d+\.\s+(.+)/);
    const tipo = itemUl ? "ul" : itemOl ? "ol" : null;
    if (tipo) {
      if (listaAtual !== tipo) {
        if (listaAtual) saida.push(`</${listaAtual}>`);
        saida.push(`<${tipo}>`);
        listaAtual = tipo;
      }
      saida.push(`<li>${(itemUl || itemOl)[1]}</li>`);
    } else {
      if (listaAtual) { saida.push(`</${listaAtual}>`); listaAtual = null; }
      if (linha.trim()) saida.push(`<p>${linha}</p>`);
    }
  }
  if (listaAtual) saida.push(`</${listaAtual}>`);
  return saida.join("");
}

function adicionarMensagemIA(quem, texto, temporaria = false) {
  const box = document.getElementById("ia-chat-mensagens");
  const div = document.createElement("div");
  div.className = `msg ${quem}` + (temporaria ? " temp" : "");
  // Só a resposta do bot passa pelo Markdown — a pergunta é texto puro do
  // usuário, não tem por quê (nem deveria) virar HTML.
  if (quem === "bot") div.innerHTML = renderizarMarkdown(texto);
  else div.textContent = texto;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

// Janela de memória do chat: guarda só as últimas TROCAS_LEMBRADAS trocas
// (pergunta+resposta) e manda de volta a cada pergunta nova — sem isso, a
// API trata cada pergunta como uma conversa do zero (é sem estado de
// propósito, ver docstring de chatbot.responder) e "esquece" o que acabou
// de ser perguntado.
const TROCAS_LEMBRADAS = 5;
let historicoChatIA = [];

async function enviarPerguntaIA() {
  const input = document.getElementById("ia-chat-input");
  const pergunta = input.value.trim();
  if (!pergunta || !adminToken) return;
  input.value = "";

  adicionarMensagemIA("voce", pergunta);
  const temp = adicionarMensagemIA("bot", "Pensando...", true);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${adminToken}` },
      body: JSON.stringify({ pergunta, historico: historicoChatIA }),
    });
    const data = await res.json();
    temp.remove();
    if (res.ok) {
      adicionarMensagemIA("bot", data.resposta);
      historicoChatIA.push({ role: "user", content: pergunta }, { role: "assistant", content: data.resposta });
      historicoChatIA = historicoChatIA.slice(-TROCAS_LEMBRADAS * 2);
    } else {
      adicionarMensagemIA("bot", data.erro || "Não consegui responder agora.");
    }
  } catch (err) {
    temp.remove();
    adicionarMensagemIA("bot", "Sem conexão com o servidor.");
  }
}

// ─── Listeners globais ──────────────────────────────────────────────────────────
document.getElementById("btn-abrir-ia").addEventListener("click", abrirPainelIA);
document.getElementById("btn-fechar-ia").addEventListener("click", fecharPainelIA);
document.getElementById("ia-panel-backdrop").addEventListener("click", fecharPainelIA);
document.getElementById("btn-enviar-ia").addEventListener("click", enviarPerguntaIA);
document.getElementById("ia-chat-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") enviarPerguntaIA();
});
document.getElementById("btn-refresh").addEventListener("click", refresh);
document.getElementById("btn-cancel").addEventListener("click", fecharModal);
document.getElementById("btn-confirm").addEventListener("click", confirmarInicio);
document.getElementById("overlay").addEventListener("click", (e) => {
  if (e.target.id === "overlay") fecharModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { fecharModal(); fecharPainelIA(); }
});
document.getElementById("btn-login").addEventListener("click", fazerLogin);
document.getElementById("f-admin-senha").addEventListener("keydown", (e) => {
  if (e.key === "Enter") fazerLogin();
});
document.getElementById("btn-relatorio").addEventListener("click", baixarRelatorio);
document.getElementById("btn-cancelar-manutencao").addEventListener("click", fecharModalManutencao);
document.getElementById("btn-confirmar-manutencao").addEventListener("click", confirmarManutencao);
document.getElementById("overlay-manutencao").addEventListener("click", (e) => {
  if (e.target.id === "overlay-manutencao") fecharModalManutencao();
});
document.getElementById("f-motivo-manutencao").addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmarManutencao();
});

configurarTooltipGrafico("demand-chart", () => _curvaDemandaAtual, (hora, p) =>
  `<b>${hora}h</b><br>Demanda prevista: ${Math.round(p.demanda * 100)}%`
);
configurarTooltipGrafico("solar-chart", () => _curvaSolarAtual, (hora, p) =>
  `<b>${hora}h</b><br>Geração solar: ${Math.round(p.geracao_relativa * 100)}%` +
  (p.janela_solar ? `<br><span class="tt-accent">☀ janela de desconto</span>` : "")
);

// ─── Início ──────────────────────────────────────────────────────────────────────
if (adminToken) {
  iniciarApp();
} else {
  document.getElementById("f-admin-usuario").focus();
}
