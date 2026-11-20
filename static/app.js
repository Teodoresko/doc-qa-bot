// DocQA front end: no framework, no build step.
const $ = (s) => document.querySelector(s);
const SAMPLE_QUESTIONS = [
  "How do I descale the machine?",
  "What does error E04 mean?",
  "How do I connect it to Wi-Fi?",
  "What does the warranty cover?",
];

let sid;
try { sid = localStorage.getItem("docqa-sid"); } catch {}
if (!sid) {
  sid = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
  sid = sid.replace(/[^a-f0-9-]/g, "").slice(0, 36);
  try { localStorage.setItem("docqa-sid", sid); } catch {}
}
const headers = { "X-Session": sid };
let history = [];
let busy = false;

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Tiny markdown: paragraphs, bullet/numbered lists, **bold**, `code`, [n] citations.
function render(md, msgId) {
  const inline = (t) => esc(t)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[(\d{1,2})\]/g, `<button class="cite" data-msg="${msgId}" data-n="$1">$1</button>`);
  const out = []; let list = null;
  for (const raw of md.split("\n")) {
    const line = raw.trim();
    const ul = line.match(/^[-*•]\s+(.*)/), ol = line.match(/^\d+[.)]\s+(.*)/);
    if (ul || ol) {
      const tag = ul ? "ul" : "ol";
      if (list !== tag) { if (list) out.push(`</${list}>`); out.push(`<${tag}>`); list = tag; }
      out.push(`<li>${inline((ul || ol)[1])}</li>`);
      continue;
    }
    if (list) { out.push(`</${list}>`); list = null; }
    if (line) out.push(`<p>${inline(line.replace(/^#+\s*/, ""))}</p>`);
  }
  if (list) out.push(`</${list}>`);
  return out.join("");
}

function scrollDown() { const m = $("#messages"); m.scrollTop = m.scrollHeight; }

function addMsg(role, html, cls = "") {
  $("#empty")?.remove();
  const el = document.createElement("div");
  el.className = `msg ${role} ${cls}`;
  el.innerHTML = `<div class="bubble">${html}</div>`;
  $("#messages").appendChild(el);
  scrollDown();
  return el;
}

const fileUrl = (s) => `/api/file/${s.doc_id}?session=${encodeURIComponent(sid)}#page=${s.page}`;

function addAnswer(data) {
  const id = "m" + Date.now();
  const el = addMsg("bot", render(data.answer, id));
  el.id = id;
  if (data.sources?.length) {
    const box = document.createElement("div");
    box.className = "sources";
    box.innerHTML = data.sources.map((s) => `
      <div class="src" data-n="${s.n}">
        <div class="src-head"><span class="n">[${s.n}]</span>
          <span class="file" title="${esc(s.file)}">${esc(s.file)}</span>
          <a href="${fileUrl(s)}" target="_blank" rel="noopener">Page ${s.page} ↗</a></div>
        <div class="src-text">${esc(s.text)}</div>
      </div>`).join("");
    el.appendChild(box);
  }
  const foot = document.createElement("div");
  foot.className = "foot";
  foot.textContent = `${data.model || ""} · ${(data.ms / 1000).toFixed(1)} s`;
  el.appendChild(foot);
  scrollDown();
}

// Clicking [n] highlights the matching source card.
document.addEventListener("click", (e) => {
  const c = e.target.closest(".cite");
  if (c) {
    const card = document.querySelector(`#${c.dataset.msg} .src[data-n="${c.dataset.n}"]`);
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "nearest" });
      card.classList.add("flash"); setTimeout(() => card.classList.remove("flash"), 1200);
    }
  }
  const t = e.target.closest(".src-text");
  if (t) t.classList.toggle("open");
});

async function ask(q) {
  if (busy || !q.trim()) return;
  busy = true; $("#send").disabled = true;
  addMsg("user", esc(q));
  const wait = addMsg("bot", `<span class="typing"><span></span><span></span><span></span></span>`);
  try {
    const r = await fetch("/api/ask", {
      method: "POST", headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, history }),
    });
    const data = await r.json();
    wait.remove();
    if (!r.ok) throw new Error(data.detail || "Request failed");
    addAnswer(data);
    history.push({ role: "user", content: q }, { role: "assistant", content: data.answer });
    history = history.slice(-8);
  } catch (err) {
    wait.remove();
    addMsg("bot", esc(String(err.message || err)), "error");
  } finally {
    busy = false; $("#send").disabled = false; $("#q").focus();
  }
}

async function loadStatus() {
  const r = await fetch("/api/status", { headers });
  const s = await r.json();
  $("#limits").textContent = `PDF · up to ${s.limits.max_mb} MB · ${s.limits.max_files} files`;
  $("#docs").innerHTML = s.docs.map((d) => `
    <li><span class="pdf">PDF</span>
      <span class="name"><a href="/api/file/${d.doc_id}?session=${encodeURIComponent(sid)}" target="_blank" rel="noopener" title="${esc(d.file)}">${esc(d.file)}</a>
        <div class="meta">${d.pages} pages</div></span>
      ${d.sample ? `<span class="tag">Sample</span>` : `<button data-del="${d.doc_id}" title="Remove">×</button>`}
    </li>`).join("");
  const eng = { gemini: "Google Gemini", claude: "Anthropic Claude", "claude-cli": "Claude (local CLI)", none: "No LLM key (search-only)" }[s.provider] || s.provider;
  $("#engine").innerHTML = `Model: <b>${esc(eng)}</b> <span>${esc(s.model)}</span><br>
    Retrieval: <b>${s.vector_search ? "Hybrid (BM25 + embeddings)" : "Keyword (BM25)"}</b>`;
}

async function upload(file) {
  const st = $("#upload-status");
  st.className = "upload-status"; st.textContent = `Reading ${file.name}…`;
  const fd = new FormData(); fd.append("file", file);
  try {
    const r = await fetch("/api/upload", { method: "POST", headers, body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "Upload failed");
    st.textContent = `Added ${d.file}: ${d.pages} pages, ${d.chunks} chunks.`;
    await loadStatus();
  } catch (e) {
    st.className = "upload-status err"; st.textContent = e.message;
  }
}

$("#docs").addEventListener("click", async (e) => {
  const id = e.target.dataset?.del;
  if (!id) return;
  await fetch(`/api/docs/${id}`, { method: "DELETE", headers });
  loadStatus();
});
$("#file").addEventListener("change", (e) => { if (e.target.files[0]) upload(e.target.files[0]); e.target.value = ""; });
const dz = $("#dropzone");
["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
dz.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) upload(f); });

const q = $("#q");
q.addEventListener("input", () => { q.style.height = "auto"; q.style.height = q.scrollHeight + "px"; });
q.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#form").requestSubmit(); } });
$("#form").addEventListener("submit", (e) => { e.preventDefault(); const v = q.value; q.value = ""; q.style.height = "auto"; ask(v); });
$("#clear").addEventListener("click", () => location.reload());
$("#menu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));

$("#chips").innerHTML = SAMPLE_QUESTIONS.map((x) => `<button type="button">${esc(x)}</button>`).join("");
$("#chips").addEventListener("click", (e) => { if (e.target.tagName === "BUTTON") ask(e.target.textContent); });
loadStatus();
