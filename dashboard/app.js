/* Reflow dashboard: same-origin HTTP, named SSE events, no network libraries. */
(function () {
  "use strict";
  const STEP_LABELS = ["Ollama local", "Extração", "Documentação", "Classificação", "Segurança", "Robin", "Relatório"];
  const STEP_ICONS = ["◈", "⇣", "✦", "◇", "⛨", "⌁", "▤"];
  const STEP_TONES = ["cyan", "teal", "violet", "pink", "green", "amber", "blue"];
  const STATUS = {idle: "Aguardando", running: "Em execução", completed: "Teste encerrado", error: "Erro no teste", cancelled: "Cancelado"};
  function metrics(snapshot) {
    const steps = snapshot.steps || [];
    const count = (status) => steps.filter(step => step.status === status).length;
    const completed = count("completed"), errors = count("error"), skipped = count("skipped");
    return {completed, errors, skipped, total: steps.length,
      progress: steps.length ? Math.round((completed + errors + skipped) * 100 / steps.length) : 0};
  }
  // Pure helpers are also exercised using Node's built-in test runner, without npm.
  if (typeof module !== "undefined" && module.exports) module.exports = {metrics, STATUS};
  if (typeof document === "undefined") return;
  const ui = {};
  const state = {csrf: null, health: false, pending: false, source: null,
    snapshot: {status: "idle", steps: [], projects: []}, localLogs: [], project: null,
    lastLogKey: "", hiddenBefore: 0, following: true};

  function text(id, value) { ui[id].textContent = value; }
  function notice(message, isFile = false) {
    ui.notice.hidden = !message;
    ui.notice.textContent = message || "";
    if (isFile) {
      const link = document.createElement("a");
      link.href = "http://127.0.0.1:8765/"; link.textContent = " Abrir dashboard pelo servidor →";
      ui.notice.append(link);
    }
  }
  function log(level, message) {
    if (state.localLogs.at(-1)?.message === message) return;
    state.localLogs.push({level, message, time: Date.now() / 1000});
    state.localLogs = state.localLogs.slice(-20); renderLogs();
  }
  function renderLogs() {
    const logs = [...(state.snapshot.logs || []), ...state.localLogs]
      .filter(item => item.time > state.hiddenBefore).sort((a, b) => a.time - b.time).slice(-150);
    const key = JSON.stringify(logs);
    if (key === state.lastLogKey) return;
    state.lastLogKey = key;
    ui["logs-container"].replaceChildren();
    if (!logs.length) {
      const item = document.createElement("li"); item.className = "empty-log";
      item.textContent = "Aguardando eventos reais do teste."; ui["logs-container"].append(item);
    }
    for (const entry of logs) {
      const item = document.createElement("li"); item.className = "log"; item.dataset.level = entry.level;
      const time = document.createElement("time");
      time.textContent = new Date(entry.time * 1000).toLocaleTimeString("pt-BR");
      const content = document.createElement("div");
      if (entry.project) { const label = document.createElement("p"); label.className = "log-project";
        label.textContent = entry.project; content.append(label); }
      const message = document.createElement("p"); message.textContent = entry.message;
      content.append(message); item.append(time, content); ui["logs-container"].append(item);
    }
    ui["logs-container"].scrollTop = ui["logs-container"].scrollHeight;
  }
  function buttons() {
    const busy = state.pending || state.snapshot.active;
    ui["run-btn"].disabled = busy || !state.csrf || !state.health;
    ui["run-btn"].dataset.busy = String(Boolean(busy));
    ui["run-btn"].textContent = busy ? "Pipeline em andamento…" : "▶  Executar pipeline local  ↗";
    ui["cancel-btn"].hidden = !state.snapshot.active;
    ui["project-select"].disabled = Boolean(busy);
  }
  function options(element, projects, placeholder) {
    const value = element.value;
    const signature = JSON.stringify(projects);
    if (element.dataset.projects === signature) return;
    element.dataset.projects = signature;
    element.replaceChildren();
    if (placeholder) { const option = document.createElement("option"); option.value = "";
      option.textContent = placeholder; element.append(option); }
    projects.forEach(project => { const option = document.createElement("option");
      option.value = project; option.textContent = project; element.append(option); });
    if (projects.includes(value)) element.value = value;
  }
  function renderSteps() {
    const snapshot = state.snapshot;
    const active = snapshot.steps.find(step => step.status === "running");
    if (active && state.following) state.project = active.project;
    if (!snapshot.projects.includes(state.project)) state.project = snapshot.projects[0];
    options(ui["project-view"], snapshot.projects, snapshot.projects.length ? null : "Nenhum teste iniciado");
    if (state.project) ui["project-view"].value = state.project;
    let steps = snapshot.steps.filter(step => step.project === state.project);
    if (!steps.length) steps = STEP_LABELS.map(label => ({label, status: "pending"}));
    const list = ui["steps-container"];
    const animate = list.dataset.count !== String(steps.length);
    list.dataset.count = String(steps.length);
    list.dataset.animate = String(animate);
    list.replaceChildren();
    for (const [index, step] of steps.entries()) {
      const item = document.createElement("li");
      item.className = "stage spotlight";
      item.dataset.state = step.status;
      item.dataset.tone = STEP_TONES[index % STEP_TONES.length];
      if (step.status === "running") item.setAttribute("aria-current", "step");
      const top = document.createElement("div"); top.className = "stage-top";
      const number = document.createElement("span"); number.className = "stage-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const icon = document.createElement("span"); icon.className = "stage-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = {completed: "✓", error: "!", skipped: "–", pending: STEP_ICONS[index % STEP_ICONS.length], running: ""}[step.status];
      top.append(number, icon);
      const label = document.createElement("strong"); label.textContent = step.label;
      const status = document.createElement("small");
      status.textContent = {pending: "Aguardando", running: "Executando", completed: "Concluída",
        error: "Falhou", skipped: "Não executada / N.A."}[step.status];
      item.title = step.detail || step.label; item.append(top, label, status); ui["steps-container"].append(item);
    }
    text("current-step-detail", active ? `${active.project} · ${active.detail}` :
      snapshot.status === "idle" ? "Eventos reais do servidor, sem progresso simulado." :
      snapshot.logs?.at(-1)?.message || "Aguardando atualização.");
    document.querySelector(".pipeline-panel").dataset.active = String(Boolean(snapshot.active));
  }
  function applySnapshot(snapshot) {
    if (!snapshot || !Array.isArray(snapshot.steps) || !Array.isArray(snapshot.projects)) return;
    if (snapshot.revision < (state.snapshot.revision || 0)) return;
    state.snapshot = snapshot;
    const info = metrics(snapshot);
    text("pipeline-status", STATUS[snapshot.status] || "Estado desconhecido");
    ui["pipeline-status"].dataset.state = snapshot.status;
    text("projects-count", snapshot.projects.length || (ui["project-select"].options.length - 1));
    text("steps-count", `${info.completed + info.errors + info.skipped} / ${info.total}`);
    text("stats-completed", info.completed); text("stats-errors", info.errors); text("stats-skipped", info.skipped);
    ui["progress-fill"].value = info.progress; text("progress-number", `${info.progress}%`);
    text("progress-label", snapshot.active ? "Acompanhando o teste ao vivo" : STATUS[snapshot.status] || "Aguardando");
    renderSteps(); renderLogs(); buttons(); elapsed();
  }
  function elapsed() {
    const snapshot = state.snapshot;
    const seconds = snapshot.started_at ? Math.max(0, Math.floor(((snapshot.finished_at || Date.now() / 1000) - snapshot.started_at))) : null;
    text("stats-duration", seconds === null ? "—" : `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`);
  }
  async function request(path, options = {}) {
    const abort = new AbortController(); const timer = setTimeout(() => abort.abort(), 18000);
    try {
      const response = await fetch(path, {...options, signal: abort.signal, cache: "no-store"});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      return data;
    } finally { clearTimeout(timer); }
  }
  async function refresh() {
    try {
      const data = await request("/api/status");
      state.csrf = data.csrf; state.health = Boolean(data.ollama.available);
      text("ollama-status", state.health ? "Ollama disponível" : "Ollama indisponível");
      ui["ollama-status"].dataset.state = state.health ? "online" : "error";
      text("llm-status", data.ollama.model); text("model-detail", data.ollama.message);
      options(ui["project-select"], data.projects, "Todos os projetos (sequencial)");
      applySnapshot(data.snapshot); notice(null);
    } catch (_) {
      state.csrf = null; state.health = false; buttons();
      notice("Não foi possível falar com o servidor do dashboard. Confira o terminal; nenhuma execução foi confirmada.");
    }
  }
  function connect() {
    state.source = new EventSource("/api/events");
    state.source.addEventListener("open", () => {
      text("connection-status", "Eventos conectados"); ui["connection-status"].dataset.state = "online";
      // A reconnect must never launch another run.
    });
    for (const name of ["snapshot", "update"]) state.source.addEventListener(name, event => {
      try { applySnapshot(JSON.parse(event.data).snapshot); }
      catch (_) { log("error", "Evento inválido recebido; consultando estado novamente."); refresh(); }
    });
    state.source.addEventListener("error", () => {
      text("connection-status", "Reconectando eventos…"); ui["connection-status"].dataset.state = "error";
      // EventSource reconnects and /api/status reconciles the real state; do not invent a failed run.
    });
  }
  async function startRun() {
    if (state.pending || state.snapshot.active || !state.csrf) return;
    state.pending = true; state.following = true; buttons();
    try {
      const project = ui["project-select"].value;
      await request("/api/run", {method: "POST", headers: {"Content-Type": "application/json", "X-Reflow-Token": state.csrf},
        body: JSON.stringify(project ? {project} : {all: true})});
      await refresh();
    } catch (error) { log("error", `Início não confirmado: ${error.message}`); }
    finally { state.pending = false; buttons(); }
  }
  document.addEventListener("DOMContentLoaded", async () => {
    for (const id of ["notice", "connection-status", "ollama-status", "llm-status", "model-detail", "project-select",
      "run-btn", "cancel-btn", "clear-btn", "project-view", "pipeline-status", "projects-count", "steps-count",
      "stats-duration", "stats-completed", "stats-errors", "stats-skipped", "progress-fill", "progress-number",
      "progress-label", "steps-container", "logs-container", "current-step-detail"]) {
      ui[id] = document.getElementById(id);
      if (!ui[id]) { console.error(`Elemento obrigatório ausente: ${id}`); return; }
    }
    if (location.protocol === "file:") {
      notice("Este HTML precisa do servidor HTTP para acessar os testes e eventos. Não abra o arquivo diretamente.", true);
      return;
    }
    ui["run-btn"].addEventListener("click", startRun);
    ui["cancel-btn"].addEventListener("click", async () => {
      try { await request("/api/cancel", {method: "POST", headers: {"Content-Type": "application/json", "X-Reflow-Token": state.csrf},
        body: JSON.stringify({run_id: state.snapshot.run_id})}); log("info", "Cancelamento solicitado."); }
      catch (_) { log("error", "Não foi possível confirmar o cancelamento."); }
    });
    ui["clear-btn"].addEventListener("click", () => { state.hiddenBefore = Date.now() / 1000; renderLogs(); });
    ui["project-view"].addEventListener("change", () => { state.project = ui["project-view"].value; state.following = false; renderSteps(); });
    renderSteps(); await refresh(); connect(); setInterval(refresh, 12000); setInterval(elapsed, 1000);
  });
}());
