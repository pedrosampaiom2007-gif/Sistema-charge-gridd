// ─── Configuração ────────────────────────────────────────────────────────────
// file:// ou localhost = ambiente de teste local, aponta pra API local;
// qualquer outro host (site publicado) aponta pra API publicada no Render.
const API_BASE = (location.protocol === "file:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "http://localhost:5000"
  : "https://chargegrid-api.onrender.com";

let placaAtual = null;

// ─── Helpers ──────────────────────────────────────────────────────────────────
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

// ─── Login por placa (mesma identidade do totem — sem senha) ──────────────────
async function fazerLogin() {
  const placa = document.getElementById("f-placa").value.trim().toUpperCase();
  const errEl = document.getElementById("login-error");
  const btn = document.getElementById("btn-login");
  errEl.textContent = "";

  if (!placa) { errEl.textContent = "Digite sua placa."; return; }

  const textoOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Entrando...";

  try {
    const res = await fetch(`${API_BASE}/api/usuarios/${placa}/historico`);
    if (!res.ok) { errEl.textContent = "Erro ao consultar a placa."; return; }
    const data = await res.json();

    placaAtual = placa;
    document.getElementById("placa-label").textContent = placa;
    document.getElementById("overlay-login").classList.remove("open");
    renderHistorico(data.sessoes);
  } catch (err) {
    errEl.textContent = "Sem conexão com o servidor. A API está rodando?";
  } finally {
    btn.disabled = false;
    btn.textContent = textoOriginal;
  }
}

// ─── Atualizar histórico (sem precisar recarregar a página) ───────────────────
async function atualizarHistorico() {
  if (!placaAtual) return;
  const btn = document.getElementById("btn-atualizar-historico");
  const textoOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Atualizando...";

  try {
    const res = await fetch(`${API_BASE}/api/usuarios/${placaAtual}/historico`);
    const data = await res.json();
    renderHistorico(data.sessoes);
  } catch (err) {
    showToast("Sem conexão com o servidor.");
  } finally {
    btn.disabled = false;
    btn.textContent = textoOriginal;
  }
}

// ─── Histórico de pagamentos ────────────────────────────────────────────────
function renderHistorico(sessoes) {
  const container = document.getElementById("historico-list");

  if (!sessoes.length) {
    container.innerHTML = `<div class="empty">Nenhuma sessão encontrada para essa placa ainda.</div>`;
    return;
  }

  // Só mostra de qual carro é cada sessão se a conta tiver mais de um —
  // pra quem só tem uma placa, isso seria repetir a mesma informação toda hora.
  const placasDistintas = new Set(sessoes.map((s) => s.placa));
  const mostrarPlaca = placasDistintas.size > 1;

  container.innerHTML = sessoes.map((s) => `
    <div class="sessao-card">
      ${mostrarPlaca ? `<div class="linha"><span class="k">Carro</span><span class="v cyan">${s.placa}</span></div>` : ""}
      <div class="linha"><span class="k">Data</span><span class="v">${s.data}</span></div>
      <div class="linha"><span class="k">Estação</span><span class="v">EST-${String(s.estacao).padStart(2, "0")}</span></div>
      <div class="linha"><span class="k">Horário</span><span class="v">${s.hora_inicio}h</span></div>
      <div class="linha"><span class="k">Consumo</span><span class="v">${s.kwh.toFixed(2)} kWh</span></div>
      <div class="linha"><span class="k">Valor</span><span class="v">${fmtMoeda(s.valor)}</span></div>
      <div class="linha"><span class="k">Pagamento</span><span class="v ${s.status_pagamento === "PAGO" ? "pago" : "pendente"}">${s.pagamento} · ${s.status_pagamento}</span></div>
    </div>
  `).join("");
}

// ─── Adicionar outro carro à conta ──────────────────────────────────────────
function abrirAddCarro() {
  document.getElementById("add-carro-box").hidden = false;
  document.getElementById("f-placa-nova").value = "";
  document.getElementById("add-carro-error").textContent = "";
  document.getElementById("f-placa-nova").focus();
}

function fecharAddCarro() {
  document.getElementById("add-carro-box").hidden = true;
}

async function confirmarAddCarro() {
  const placaNova = document.getElementById("f-placa-nova").value.trim().toUpperCase();
  const errEl = document.getElementById("add-carro-error");
  const btn = document.getElementById("btn-confirmar-add-carro");
  errEl.textContent = "";

  if (!placaNova) { errEl.textContent = "Digite a placa do outro carro."; return; }

  const textoOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Vinculando...";

  try {
    const res = await fetch(`${API_BASE}/api/usuarios/vincular`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ placa_existente: placaAtual, placa_nova: placaNova }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Não foi possível vincular."; return; }

    fecharAddCarro();
    showToast(`${placaNova} vinculada à sua conta.`);
    atualizarHistorico();
  } catch (err) {
    errEl.textContent = "Sem conexão com o servidor.";
  } finally {
    btn.disabled = false;
    btn.textContent = textoOriginal;
  }
}

// ─── Chat ────────────────────────────────────────────────────────────────────
function adicionarMensagem(quem, texto, temporaria = false) {
  const box = document.getElementById("chat-mensagens");
  const div = document.createElement("div");
  div.className = `msg ${quem}` + (temporaria ? " temp" : "");
  div.textContent = texto;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

async function enviarPergunta() {
  const input = document.getElementById("chat-input");
  const pergunta = input.value.trim();
  if (!pergunta) return;
  input.value = "";

  adicionarMensagem("voce", pergunta);
  const temp = adicionarMensagem("bot", "Pensando...", true);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
    const data = await res.json();
    temp.remove();
    adicionarMensagem("bot", res.ok ? data.resposta : (data.erro || "Não consegui responder agora."));
  } catch (err) {
    temp.remove();
    adicionarMensagem("bot", "Sem conexão com o servidor.");
  }
}

// ─── Listeners ──────────────────────────────────────────────────────────────
document.getElementById("btn-login").addEventListener("click", fazerLogin);
document.getElementById("f-placa").addEventListener("keydown", (e) => {
  if (e.key === "Enter") fazerLogin();
});
document.getElementById("btn-atualizar-historico").addEventListener("click", atualizarHistorico);
document.getElementById("btn-add-carro").addEventListener("click", abrirAddCarro);
document.getElementById("btn-cancelar-add-carro").addEventListener("click", fecharAddCarro);
document.getElementById("btn-confirmar-add-carro").addEventListener("click", confirmarAddCarro);
document.getElementById("f-placa-nova").addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmarAddCarro();
});
document.getElementById("btn-enviar-chat").addEventListener("click", enviarPergunta);
document.getElementById("chat-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") enviarPergunta();
});
document.getElementById("f-placa").focus();
