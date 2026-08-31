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

let placaAtual = null;
let pinAtual = null; // guardado só em memória, reaproveitado por "+ Adicionar carro"
let modoCadastroLogin = false; // true = tela de login virou "cadastre-se"

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

// ─── Alterna a tela de login entre "entrar" e "cadastrar-se" ──────────────────
// Não é uma tela separada — é o mesmo formulário, só revelando o campo de nome.
// Sem isso, quem abre o app direto (sem nunca ter passado pelo totem) fica
// sem nenhum jeito de virar cliente.
function alternarModoCadastro() {
  modoCadastroLogin = !modoCadastroLogin;
  document.getElementById("campo-nome-cadastro").hidden = !modoCadastroLogin;
  document.getElementById("btn-login").textContent = modoCadastroLogin ? "Cadastrar e entrar" : "Entrar";
  document.getElementById("link-cadastro").textContent = modoCadastroLogin
    ? "Já sou cadastrado"
    : "Ainda não tem cadastro? Cadastre-se";
  document.getElementById("login-error").textContent = "";
  document.getElementById(modoCadastroLogin ? "f-nome-cadastro" : "f-placa").focus();
}

// ─── Login por placa + PIN ──────────────────────────────────────────────────
// PIN existe porque, sem ele, bastava saber a placa (sem segredo nenhum)
// pra ver o histórico de pagamento de qualquer motorista.
async function fazerLogin() {
  const placa = document.getElementById("f-placa").value.trim().toUpperCase();
  const pin = document.getElementById("f-pin").value.trim();
  const errEl = document.getElementById("login-error");
  const btn = document.getElementById("btn-login");
  errEl.textContent = "";

  if (!placa) { errEl.textContent = "Digite sua placa."; return; }
  if (!/^\d{4}$/.test(pin)) { errEl.textContent = "O PIN precisa ter exatamente 4 números."; return; }

  btn.disabled = true;

  try {
    if (modoCadastroLogin) {
      const nome = document.getElementById("f-nome-cadastro").value.trim();
      if (!nome) { errEl.textContent = "Digite seu nome pra concluir o cadastro."; return; }

      btn.textContent = "Cadastrando...";
      const resCadastro = await fetch(`${API_BASE}/api/usuarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ placa, nome, pin }),
      });
      const dataCadastro = await resCadastro.json();
      if (!resCadastro.ok) { errEl.textContent = dataCadastro.erro || "Não foi possível cadastrar."; return; }
    }

    btn.textContent = "Entrando...";
    const res = await fetch(`${API_BASE}/api/usuarios/historico`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ placa, pin }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.erro || "Placa ou PIN incorretos."; return; }

    placaAtual = placa;
    pinAtual = pin;
    document.getElementById("placa-label").textContent = placa;
    document.getElementById("overlay-login").classList.remove("open");
    renderHistorico(data.sessoes);
  } catch (err) {
    errEl.textContent = "Sem conexão com o servidor. A API está rodando?";
  } finally {
    btn.disabled = false;
    btn.textContent = modoCadastroLogin ? "Cadastrar e entrar" : "Entrar";
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
    const res = await fetch(`${API_BASE}/api/usuarios/historico`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ placa: placaAtual, pin: pinAtual }),
    });
    const data = await res.json();
    // Sem esse if, uma resposta de erro (ex: 429 do limite de 20 consultas
    // por minuto) caía em renderHistorico(undefined) e estourava TypeError:
    // a tela simplesmente parava de atualizar sem dizer nada.
    if (!res.ok) { showToast(data.erro || "Não foi possível atualizar agora."); return; }
    renderHistorico(data.sessoes);
    document.getElementById("cashback-total").textContent = fmtMoeda(data.cashback_total || 0);
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
      ${s.cashback > 0 ? `<div class="linha"><span class="k">Cashback</span><span class="v cyan">+ ${fmtMoeda(s.cashback)}</span></div>` : ""}
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
      body: JSON.stringify({ placa_existente: placaAtual, placa_nova: placaNova, pin: pinAtual }),
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
// Escapa HTML antes de qualquer coisa: o texto vem de um modelo de IA, nunca
// deve virar HTML/script executável no navegador do motorista.
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

function adicionarMensagem(quem, texto, temporaria = false) {
  const box = document.getElementById("chat-mensagens");
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
// de ser perguntado. Fica só na aba: fechar/atualizar a página reseta,
// igual o resto do estado da tela.
const TROCAS_LEMBRADAS = 5;
let historicoChat = [];

async function enviarPergunta() {
  const input = document.getElementById("chat-input");
  const pergunta = input.value.trim();
  if (!pergunta) return;
  input.value = "";

  adicionarMensagem("voce", pergunta);
  const temp = adicionarMensagem("bot", "Pensando...", true);

  try {
    // Manda a placa/PIN de quem já está logado, senão o chat não tem como
    // saber de quem é "meu gasto" e mistura com o faturamento do sistema.
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta, placa: placaAtual, pin: pinAtual, historico: historicoChat }),
    });
    const data = await res.json();
    temp.remove();
    if (res.ok) {
      adicionarMensagem("bot", data.resposta);
      historicoChat.push({ role: "user", content: pergunta }, { role: "assistant", content: data.resposta });
      historicoChat = historicoChat.slice(-TROCAS_LEMBRADAS * 2);
    } else {
      adicionarMensagem("bot", data.erro || "Não consegui responder agora.");
    }
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
document.getElementById("f-pin").addEventListener("keydown", (e) => {
  if (e.key === "Enter") fazerLogin();
});
document.getElementById("link-cadastro").addEventListener("click", (e) => {
  e.preventDefault();
  alternarModoCadastro();
});
document.getElementById("f-nome-cadastro").addEventListener("keydown", (e) => {
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
