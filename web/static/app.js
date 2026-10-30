/* InvoiceMatch web demo. Plain JavaScript, no build step.
   All dynamic text is inserted with textContent (never as HTML), so invoice text can't inject markup. */
"use strict";

const state = { mode: "claude", config: null, samples: [], last: null, persona: 1, tab: "check" };
const PERSONAS = [
  { actor: "Tom Becker", role: "ap_specialist" },
  { actor: "Priya Natarajan", role: "ap_manager" },
  { actor: "Omar Haddad", role: "finance_controller" },
  { actor: "Diana Reyes", role: "cfo" },
  { actor: "Kevin Osei", role: "security" },
];
const ROUTES = {
  auto_approve: { stamp: "Approved", tone: "green", who: "nobody: approved automatically and released to the normal payment run." },
  approval_ap_manager: { stamp: "Needs approval", tone: "amber", who: "the AP Manager (one click)" },
  approval_finance_controller: { stamp: "Needs approval", tone: "amber", who: "the Finance Controller" },
  approval_cfo: { stamp: "Needs approval", tone: "amber", who: "the CFO" },
  review: { stamp: "Review", tone: "red", who: "a person in the AP team" },
  security_review: { stamp: "Security hold", tone: "red", who: "Information Security" },
};
const DOCS = [
  ["Discovery: stakeholders, interviews, current workflow", "discovery/README.md"],
  ["Scoping: scope, SMART metrics, business case", "scoping/README.md"],
  ["Sample data and test cases", "data/README.md"],
  ["Benchmark results", "eval/results"],
];

/* ------------------------------------------------------------------ helpers */
function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}
const $ = (sel) => document.querySelector(sel);
const money = (v, cur) => (v === null || v === undefined) ? "unreadable" :
  (cur && cur !== "USD" ? cur + " " : "$") + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (v) => (v === null || v === undefined) ? "-" : (v * 100).toFixed(v === 1 || v === 0 ? 0 : 1) + "%";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function store(key, value) {
  try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch (e) { return null; }
  return null;
}
function visitorId() {
  let id = store("im_visitor");
  if (!id || !/^[a-f0-9]{32}$/.test(id)) {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    id = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
    store("im_visitor", id);
  }
  return id;
}
const VISITOR = visitorId();

async function api(path, options = {}) {
  const res = await fetch(path, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json", "X-Visitor": VISITOR },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    const err = new Error((data && data.error) || `Request failed (${res.status})`);
    err.status = res.status; err.data = data;
    throw err;
  }
  return data;
}

let toastTimer = null;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 4200);
}

/* ------------------------------------------------------------------ tabs and mode */
function showTab(name) {
  state.tab = name;
  document.querySelectorAll(".tab").forEach((b) => {
    const on = b.dataset.tab === name;
    b.classList.toggle("is-on", on); b.setAttribute("aria-selected", on);
  });
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("is-on", p.id === "tab-" + name));
  if (name === "queue") loadQueue();
  if (name === "audit") loadAudit();
  if (name === "metrics") loadMetrics();
  store("im_tab", name);
}
function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".mode-btn").forEach((b) => {
    const on = b.dataset.mode === mode;
    b.classList.toggle("is-on", on); b.setAttribute("aria-checked", on);
  });
  const read = document.querySelector('.steps li[data-step="read"] span');
  read.textContent = mode === "claude" ? "Claude via SharedLLM" : "fixed patterns (no AI)";
  store("im_mode", mode);
}

/* ------------------------------------------------------------------ samples */
function fillSamples() {
  const sel = $("#sample-select");
  sel.replaceChildren(h("option", { value: "", text: "Choose a sample invoice..." }));
  const groups = [
    ["sample", "Sample invoices (28): every rule tested"],
    ["new_layout", "New layouts (12): written after the rules reader was built"],
  ];
  for (const [g, label] of groups) {
    const og = h("optgroup", { label });
    for (const s of state.samples.filter((x) => x.group === g)) {
      og.append(h("option", { value: s.id, text: `${s.id.startsWith("H") ? s.id : "#" + s.id}  ${s.title}` }));
    }
    sel.append(og);
  }
}
function pickSample(id) {
  const s = state.samples.find((x) => x.id === id);
  if (!s) return;
  $("#sample-select").value = id;
  $("#invoice-text").value = s.text;
  $("#sample-title").textContent = `What it tests: ${s.title}`;
  document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("is-on", c.dataset.sample === id));
  updateCount();
}
function updateCount() {
  const n = $("#invoice-text").value.length;
  const max = state.config ? state.config.limits.max_chars : 8000;
  $("#char-count").textContent = `${n.toLocaleString()} / ${max.toLocaleString()} characters`;
}

/* ------------------------------------------------------------------ check an invoice */
function setStep(name, cls, label) {
  const li = document.querySelector(`.steps li[data-step="${name}"]`);
  li.classList.remove("run", "done", "warn");
  if (cls) li.classList.add(cls);
  if (label) li.querySelector("span").textContent = label;
}
function resetSteps() {
  setStep("parse", null, "bank details removed");
  setStep("read", null, state.mode === "claude" ? "Claude via SharedLLM" : "fixed patterns (no AI)");
  setStep("ground", null, "values found in text?");
  setStep("match", null, "10 checks");
  setStep("decide", null, "approval rules");
  setStep("audit", null, "audit log + ERP");
}

async function checkInvoice() {
  const text = $("#invoice-text").value;
  if (!text.trim()) { toast("Pick a sample invoice or paste invoice text first."); return; }
  const btn = $("#check-btn");
  btn.disabled = true; btn.textContent = "Checking...";
  resetSteps();
  setStep("parse", "run"); setStep("read", "run", state.mode === "claude" ? "Claude is reading..." : "reading...");
  $("#result-body").className = "";
  $("#result-body").replaceChildren(h("p", { class: "hint", text: "Working... Claude usually takes 2-3 seconds." }));
  try {
    const r = await api("/api/process", { method: "POST", body: { text, mode: state.mode } });
    await animateSteps(r);
    renderResult(r);
    refreshQueueCount();
    refreshAiStatus();
  } catch (e) {
    resetSteps();
    $("#result-body").replaceChildren(h("div", { class: "notice", text: e.message }));
  } finally {
    btn.disabled = false; btn.textContent = "Check invoice";
  }
}

async function animateSteps(r) {
  const failed = r.checks.filter((c) => c.status === "fail").length;
  const ai = r.read_by === "claude" && r.llm && r.llm.ok;
  setStep("parse", "done", r.bank_found ? "bank removed" : "no bank details");
  await sleep(150);
  setStep("read", ai ? "done" : "warn", ai ? `${r.llm.input_tokens + r.llm.output_tokens} tokens` : "by rules");
  await sleep(150);
  const grounded = r.issues.filter((i) => i.includes("not found in the invoice text")).length;
  setStep("ground", grounded ? "warn" : "done", grounded ? `${grounded} discarded` : "all found");
  await sleep(150);
  setStep("match", failed ? "warn" : "done", failed ? `${failed} failed` : "10/10 passed");
  await sleep(150);
  setStep("decide", ROUTES[r.decision.route].tone === "red" ? "warn" : "done", r.decision.rule_ids.join(", "));
  await sleep(150);
  setStep("audit", "done", `record #${r.audit.seq}`);
}

function renderResult(r) {
  const route = ROUTES[r.decision.route];
  const f = r.fields;
  const body = $("#result-body");
  body.className = "";
  const parts = [];

  if (r.notice) parts.push(h("div", { class: "notice", text: r.notice }));

  parts.push(h("div", { class: "verdict" },
    h("div", { class: `stamp ${route.tone}`, text: route.stamp }),
    h("div", { class: "verdict-text" },
      h("b", { text: r.decision.label }),
      h("span", { text: `Rule${r.decision.rule_ids.length > 1 ? "s" : ""} ${r.decision.rule_ids.join(", ")} · ${r.ref}` }))));

  parts.push(h("div", { class: "summary" },
    h("div", {}, h("small", { text: "Vendor" }), h("span", { text: r.vendor_name })),
    h("div", {}, h("small", { text: "Invoice" }), h("span", { text: `${f.invoice_number || "?"} · ${f.invoice_date || "?"}` })),
    h("div", {}, h("small", { text: "Purchase order" }), h("span", { text: f.po_number || "none found" })),
    h("div", {}, h("small", { text: "Total" }), h("span", { text: money(f.total_amount, f.currency) }))));

  if (r.read_by === "claude" && r.llm && r.llm.ok) {
    parts.push(h("div", { class: "readby" },
      h("strong", { text: "Read by Claude via SharedLLM" }),
      ` · ${r.llm.model} · ${r.llm.input_tokens} in / ${r.llm.output_tokens} out tokens · $${r.llm.cost_usd.toFixed(5)} · ${(r.llm.latency_ms / 1000).toFixed(1)} s`));
  } else {
    parts.push(h("div", { class: "readby rules" },
      h("strong", { text: "Read by the rules reader (no AI)" }),
      r.fallback_reason ? ` · ${r.fallback_reason}` : " · fixed patterns for known layouts, $0"));
  }

  parts.push(h("ul", { class: "reasons" }, r.decision.reasons.map((reason) =>
    h("li", { class: r.decision.failed_rules.length ? "fail" : "ok", text: reason }))));

  parts.push(h("h2", { text: "The ten checks" }));
  parts.push(h("ul", { class: "checks" }, r.checks.map((c) =>
    h("li", { class: c.status, title: c.message },
      h("span", { class: "mark-s", text: c.status === "pass" ? "PASS" : c.status === "fail" ? "FAIL" : "SKIP" }),
      h("span", {}, `${c.rule} ${c.name}`)))));

  if (r.lines.length) {
    const rows = r.lines.map((l) => {
      const bad = (l.po_remaining !== null && l.invoice_qty > l.po_remaining) ||
        (l.price_difference_pct !== null && l.price_difference_pct > 1) || l.contract_unit_price === null;
      return h("tr", { class: bad ? "bad" : null },
        h("td", { class: "mono", text: l.sku || "?" }),
        h("td", { class: "num", text: l.invoice_qty ?? "?" }),
        h("td", { class: "num", text: l.po_remaining === null ? "-" : `${l.po_remaining} of ${l.po_ordered}` }),
        h("td", { class: "num", text: l.invoice_unit_price === null ? "?" : money(l.invoice_unit_price, f.currency) }),
        h("td", { class: "num", text: l.contract_unit_price === null ? "-" : money(l.contract_unit_price) }),
        h("td", { class: "num", text: l.price_difference_pct === null ? "-" : `${l.price_difference_pct > 0 ? "+" : ""}${l.price_difference_pct}%` }));
    });
    parts.push(h("h2", { text: "Invoice vs PO vs contract" }));
    parts.push(h("div", { class: "table-wrap" }, h("table", { class: "ledger" },
      h("thead", {}, h("tr", {}, ["Item", "Invoiced qty", "Left on PO", "Invoice price", "Contract price", "Difference"].map((t) => h("th", { text: t })))),
      h("tbody", {}, rows))));
  }

  const det = h("details", {}, h("summary", { text: "All extracted fields and notes" }));
  const dl = h("dl", { class: "fieldgrid" });
  const fieldRows = [
    ["Vendor (as printed)", f.vendor], ["Invoice number", f.invoice_number], ["Invoice date", f.invoice_date],
    ["PO number", f.po_number], ["Currency", f.currency], ["Subtotal", f.subtotal], ["Tax", f.tax],
    ["Freight / delivery", f.freight], ["Total", f.total_amount],
    ["Bank details", r.bank_found ? "found by the parser; removed before the AI call; compared with the vendor master" : "none printed"],
  ];
  for (const [k, v] of fieldRows) dl.append(h("dt", { text: k }), h("dd", { text: v === null || v === undefined ? "not found" : String(v) }));
  det.append(dl);
  for (const issue of r.issues) det.append(h("p", { class: "hint", text: "Note: " + issue }));
  det.append(h("p", { class: "hint", text: `Audit record #${r.audit.seq}, fingerprint ${r.audit.hash}...` }));
  parts.push(det);

  if (r.status === "pending") {
    parts.push(h("div", { class: "next" },
      `Next: waiting for ${route.who}. `,
      h("button", { class: "linkish", text: "Open the review queue", onclick: () => showTab("queue") })));
  } else {
    parts.push(h("div", { class: "next", text: "Next: nothing. Approved automatically under rule A-1; the ERP status was set to approved and the invoice joins the normal payment run." }));
  }
  body.replaceChildren(...parts);
}

async function refreshAiStatus() {
  try {
    const c = await api("/api/config");
    state.config.ai_remaining_today = c.ai_remaining_today;
    if (c.ai_available) $("#ai-status").textContent = `AI: ${c.model} via ${c.gateway} \u00b7 ${c.ai_remaining_today} AI reads left today` +
      (c.ai_breaker === "open" ? " \u00b7 paused after gateway errors" : "");
  } catch (e) { /* status line only */ }
}

/* ------------------------------------------------------------------ review queue */
function fillPersonas() {
  const sel = $("#persona");
  sel.replaceChildren(...PERSONAS.map((p, i) =>
    h("option", { value: String(i), text: `${p.actor} (${state.config.roles[p.role]})` })));
  sel.value = String(state.persona);
  personaHint();
}
function personaHint() {
  const p = PERSONAS[state.persona];
  const lim = state.config.limits;
  const hints = {
    ap_specialist: "Can resolve ordinary review items, with a written reason. Cannot approve amounts above the auto-approval limit.",
    ap_manager: `Can approve matched invoices up to $${lim.ap_manager.toLocaleString()} and resolve review items.`,
    finance_controller: `Can approve up to $${lim.controller.toLocaleString()} and sign off high-value mismatches.`,
    cfo: "Can approve any amount.",
    security: "Clears or rejects invoices with changed bank details. Nothing else.",
  };
  $("#persona-hint").textContent = hints[p.role];
}

async function loadQueue() {
  try {
    const q = await api("/api/queue");
    renderQueue(q);
  } catch (e) { $("#queue-list").replaceChildren(h("div", { class: "notice", text: e.message })); }
}
async function refreshQueueCount() {
  try {
    const q = await api("/api/queue");
    const pill = $("#queue-count");
    pill.textContent = q.pending.length; pill.hidden = q.pending.length === 0;
    if (state.tab === "queue") renderQueue(q);
  } catch (e) { /* the count is a convenience only */ }
}
function queueCard(item, pending) {
  const route = ROUTES[item.decision.route];
  const f = item.fields;
  const card = h("div", { class: "card qcard" });
  card.append(h("div", { class: "qhead" },
    h("div", {},
      h("div", { class: "qtitle", text: `${item.vendor_name} · ${money(f.total_amount, f.currency)}` }),
      h("div", { class: "qmeta", text: `${item.ref} · invoice ${f.invoice_number || "?"} · ${f.po_number || "no PO"} · ${item.decision.rule_ids.join(", ")}` })),
    h("div", { class: `stamp ${pending ? route.tone : item.status === "approved" ? "green" : "red"}`,
      text: pending ? route.stamp : item.status })));
  card.append(h("ul", { class: "reasons" }, item.decision.reasons.map((r) =>
    h("li", { class: item.decision.failed_rules.length ? "fail" : "ok", text: r }))));
  if (!pending) {
    card.append(h("p", { class: "hint", text: `${item.status === "approved" ? "Approved" : "Rejected"} by ${item.resolved_by || "InvoiceMatch (rule A-1)"}${item.resolution_note ? ": “" + item.resolution_note + "”" : ""}` }));
    return card;
  }
  const allowed = item.allowed_roles.map((r) => state.config.roles[r]).join(", ");
  card.append(h("p", { class: "hint", text: `Who can act: ${allowed}.` }));
  const note = h("input", { type: "text", maxlength: "300", placeholder: "Reason (required for overrides and rejections)", "aria-label": "Reason" });
  const err = h("div", { class: "qerror", hidden: true });
  const act = async (action) => {
    const p = PERSONAS[state.persona];
    try {
      await api(`/api/queue/${item.ref}/${action}`, { method: "POST", body: { actor: p.actor, role: p.role, note: note.value } });
      toast(`${item.ref} ${action === "approve" ? "approved" : "rejected"} by ${p.actor}. Logged in the audit log.`);
      loadQueue(); refreshQueueCount();
    } catch (e) {
      err.textContent = (e.status === 403 ? "Blocked: " : "") + e.message; err.hidden = false;
    }
  };
  card.append(h("div", { class: "qactions" }, note,
    h("button", { class: "btn approve", text: "Approve", onclick: () => act("approve") }),
    h("button", { class: "btn reject", text: "Reject", onclick: () => act("reject") })));
  card.append(err);
  return card;
}
function renderQueue(q) {
  const list = $("#queue-list");
  list.replaceChildren(...(q.pending.length ? q.pending.map((i) => queueCard(i, true)) :
    [h("div", { class: "card empty-q", text: "Nothing waiting. Check a few invoices with problems (for example the quick tour) and they will appear here." })]));
  $("#resolved-list").replaceChildren(...(q.resolved.length ? q.resolved.map((i) => queueCard(i, false)) :
    [h("p", { class: "hint", text: "No decisions yet." })]));
}

/* ------------------------------------------------------------------ audit */
async function loadAudit() {
  try {
    const a = await api("/api/audit");
    const tbody = $("#audit-table tbody");
    tbody.replaceChildren(...(a.records.length ? a.records.slice().reverse().map((r) =>
      h("tr", { class: r.details && r.details.tampered_demo ? "bad" : null },
        h("td", { class: "num", text: r.seq }),
        h("td", { class: "mono", text: r.at.replace("T", " ").replace("+00:00", "") }),
        h("td", { text: r.action.replace(/_/g, " ") }),
        h("td", { text: r.actor }),
        h("td", { text: r.invoice }),
        h("td", { class: "mono", text: r.hash.slice(0, 12) + "…" }))) :
      [h("tr", {}, h("td", { colspan: "6", class: "hint", text: "No records yet. Check an invoice first." }))]));
    showVerify(a.verified, a.message);
  } catch (e) { toast(e.message); }
}
function showVerify(ok, message) {
  const v = $("#verify-result");
  v.hidden = false; v.className = "verify " + (ok ? "ok" : "bad");
  v.textContent = (ok ? "✓ " : "✗ ") + message;
}

/* ------------------------------------------------------------------ metrics and how it works */
async function loadMetrics() {
  try {
    const m = await api("/api/metrics");
    const s = m.session;
    $("#session-tiles").replaceChildren(
      h("div", { class: "tile" }, h("b", { text: s.processed }), h("span", { text: "invoices checked" })),
      h("div", { class: "tile" }, h("b", { text: pct(s.no_touch_rate) }), h("span", { text: "approved with no human touch" })),
      h("div", { class: "tile" }, h("b", { text: pct(s.review_rate) }), h("span", { text: "sent to a person (review)" })),
      h("div", { class: "tile" }, h("b", { text: s.pending }), h("span", { text: "waiting in the review queue" })),
      h("div", { class: "tile" }, h("b", { text: "$" + s.ai_cost_usd.toFixed(4) }), h("span", { text: `AI cost (${s.read_by_ai} AI reads)` })),
      h("div", { class: "tile" }, h("b", { text: s.ai_latency_ms_avg ? (s.ai_latency_ms_avg / 1000).toFixed(1) + " s" : "-" }), h("span", { text: "average AI reading time" })));
    const names = { golden: "Sample invoices", holdout: "New layouts" };
    const tbody = $("#bench-table tbody");
    tbody.replaceChildren(...(m.benchmarks.length ? m.benchmarks.map((b) => h("tr", {},
      h("td", { text: names[b.set] || b.set }),
      h("td", { text: b.mode === "claude" ? "Claude via SharedLLM" : "Rules only" }),
      h("td", { class: "num", text: b.invoices }),
      h("td", { class: "num", text: pct(b.field_accuracy) }),
      h("td", { class: "num", text: `${b.correct_decisions}/${b.invoices}` }),
      h("td", { class: "num", text: b.wrong_auto_approvals }),
      h("td", { class: "num", text: "$" + Number(b.ai_cost_per_invoice_usd || 0).toFixed(5) }),
      h("td", { class: "num", text: b.ai_latency_p50_ms ? (b.ai_latency_p50_ms / 1000).toFixed(1) + " s" : "-" }))) :
      [h("tr", {}, h("td", { colspan: "8", class: "hint", text: "No benchmark results found." }))]));
  } catch (e) { toast(e.message); }
}
function fillHow() {
  const rules = state.config.rules;
  $("#rules-table tbody").replaceChildren(
    ...Object.entries(rules).map(([id, name]) => h("tr", {}, h("td", { class: "mono", text: id }), h("td", { text: name }))),
    h("tr", {}, h("td", { class: "mono", text: "A-1" }), h("td", { text: `All checks pass and total ≤ $${state.config.limits.auto_approve.toLocaleString()}: auto-approve` })),
    h("tr", {}, h("td", { class: "mono", text: "A-2" }), h("td", { text: `Up to $${state.config.limits.ap_manager.toLocaleString()}: AP Manager` })),
    h("tr", {}, h("td", { class: "mono", text: "A-3" }), h("td", { text: `Above that: Finance Controller; over $${state.config.limits.controller.toLocaleString()}: CFO` })),
    h("tr", {}, h("td", { class: "mono", text: "A-4" }), h("td", { text: "Any failed check: human review (bank change: Security)" })));
  $("#limit-auto").textContent = "$" + state.config.limits.auto_approve.toLocaleString();
  const repo = state.config.repo_url;
  $("#doc-links").replaceChildren(...DOCS.map(([label, path]) =>
    h("li", {}, h("a", { href: `${repo}/${path.includes(".") ? "blob" : "tree"}/main/${path}`, rel: "noopener", text: label }))));
  $("#repo-link").href = repo;
}

/* ------------------------------------------------------------------ start */
async function init() {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  document.querySelectorAll(".mode-btn").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => { pickSample(c.dataset.sample); checkInvoice(); }));
  $("#sample-select").addEventListener("change", (e) => pickSample(e.target.value));
  $("#invoice-text").addEventListener("input", () => { updateCount(); $("#sample-title").textContent = "Edited text"; });
  $("#check-btn").addEventListener("click", checkInvoice);
  $("#clear-btn").addEventListener("click", () => { $("#invoice-text").value = ""; $("#sample-select").value = ""; $("#sample-title").textContent = ""; updateCount(); });
  $("#persona").addEventListener("change", (e) => { state.persona = Number(e.target.value); personaHint(); });
  $("#verify-btn").addEventListener("click", loadAudit);
  $("#tamper-btn").addEventListener("click", async () => {
    try {
      const t = await api("/api/audit/tamper", { method: "POST" });
      await loadAudit();
      showVerify(t.verified, `Record #${t.edited_record} was secretly changed to say "auto_approve". ${t.message}`);
    } catch (e) { toast(e.message); }
  });
  $("#reset-btn").addEventListener("click", async () => {
    try { await api("/api/reset", { method: "POST" }); toast("Your demo workspace was reset."); loadAudit(); refreshQueueCount(); }
    catch (e) { toast(e.message); }
  });

  try {
    const [config, samples] = await Promise.all([api("/api/config"), api("/api/samples")]);
    state.config = config; state.samples = samples;
  } catch (e) {
    toast("Could not load the demo. Please reload the page.");
    return;
  }
  $("#author").textContent = state.config.author; $("#author-foot").textContent = state.config.author;
  $("#client-name").textContent = `${state.config.client} (fictional)`;
  const ai = state.config.ai_available;
  $("#ai-status").textContent = ai ? `AI: ${state.config.model} via ${state.config.gateway} · ${state.config.ai_remaining_today} AI reads left today`
    : "AI not configured on this server: invoices are read by rules";
  fillSamples(); fillPersonas(); fillHow();
  setMode(ai ? (store("im_mode") || "claude") : "rules");
  if (!ai) document.querySelector('.mode-btn[data-mode="claude"]').disabled = true;
  pickSample("01");
  refreshQueueCount();
  const savedTab = store("im_tab");
  if (savedTab && document.getElementById("tab-" + savedTab)) showTab(savedTab);
}
document.addEventListener("DOMContentLoaded", init);
