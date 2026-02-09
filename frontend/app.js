const API_BASE = (() => {
  const isHttp = window.location.protocol === "http:" || window.location.protocol === "https:";
  if (!isHttp) return "http://127.0.0.1:8000/api/v1";

  const host = window.location.hostname;
  const isLocal = host === "localhost" || host === "127.0.0.1";
  if (isLocal) return "http://127.0.0.1:8000/api/v1";

  // Production: use same-origin and let Netlify proxy /api/v1/* to Vercel.
  return `${window.location.origin}/api/v1`;
})();

let currentReportId = null;

function $(sel) { return document.querySelector(sel); }
function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  });
  for (const c of children) node.appendChild(c);
  return node;
}

function setStatus(msg) { $("#status").textContent = msg; }

function friendlyFetchError(err) {
  const msg = (err && err.message) ? String(err.message) : String(err);
  if (/Failed to fetch|NetworkError/i.test(msg)) {
    return [
      "Request failed (network/CORS).",
      "- Ensure the API is running on http://127.0.0.1:8000",
      "- Serve the frontend via http://localhost:5173 (don’t open index.html as file://)",
      "- If using 127.0.0.1 vs localhost, make sure CORS allows it",
    ].join("\n");
  }
  return msg;
}

function setVerdictBadge(verdict) {
  const badge = $("#verdictBadge");
  badge.textContent = verdict || "—";
}

async function uploadText() {
  const text = $("#textInput").value.trim();
  if (!text) return setStatus("Please paste some text.");

  setStatus("Uploading text...");

  const form = new FormData();
  form.append("payload_text", text);

  const resp = await fetch(`${API_BASE}/upload/text`, { method: "POST", body: form });
  if (!resp.ok) throw new Error(await resp.text());
  const data = await resp.json();
  currentReportId = data.report_id;

  setStatus(`Queued report ${currentReportId}. Polling...`);
  await pollReport(currentReportId);
}

async function uploadFile(inputType, fileInputId) {
  const file = $(fileInputId).files[0];
  if (!file) return setStatus("Please choose a file.");

  setStatus(`Uploading ${inputType}...`);

  const form = new FormData();
  form.append("input_type", inputType);
  form.append("file", file);

  const resp = await fetch(`${API_BASE}/upload/file`, { method: "POST", body: form });
  if (!resp.ok) throw new Error(await resp.text());
  const data = await resp.json();
  currentReportId = data.report_id;

  setStatus(`Queued report ${currentReportId}. Polling...`);
  await pollReport(currentReportId);
}

async function pollReport(reportId) {
  const start = Date.now();
  while (true) {
    const r = await fetch(`${API_BASE}/reports/${reportId}`);
    if (!r.ok) throw new Error(await r.text());
    const report = await r.json();

    if (report.status === "complete") {
      setStatus("Analysis complete.");
      renderReport(report);
      return;
    }
    if (report.status === "failed") {
      setStatus("Analysis failed.");
      renderReport(report);
      return;
    }

    const elapsed = Math.floor((Date.now() - start) / 1000);
    setStatus(`Status: ${report.status} (${elapsed}s)`);

    await new Promise((res) => setTimeout(res, 1200));
  }
}

function renderReport(report) {
  $("#report").classList.remove("hidden");

  setVerdictBadge(report.verdict);
  $("#confidence").textContent = (report.confidence ?? "—").toString();
  $("#aiLikelihood").textContent = (report.ai_likelihood ?? "—").toString();
  $("#explanation").textContent = report.explanation || "—";

  // Claims table
  const tbody = $("#claimsTable tbody");
  tbody.innerHTML = "";
  for (const row of report.key_claims || []) {
    const citations = (row.citations || []).slice(0, 3).map(c => {
      const label = `${c.publisher || "source"}${c.date ? ` (${c.date})` : ""} — ${c.credibility || ""}`.trim();
      return `<div><a href="${c.url}" target="_blank" rel="noreferrer">${label || c.url}</a><div class="small">${escapeHtml(c.snippet || "")}</div></div>`;
    }).join("<div style=\"height:8px\"></div>");

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div>${escapeHtml(row.claim_text)}</div>
        ${row.rationale ? `<div class="small" style="margin-top:6px;white-space:pre-wrap;">${escapeHtml(row.rationale)}</div>` : ""}
      </td>
      <td>${escapeHtml(row.status)}</td>
      <td>${escapeHtml(String(row.confidence))}</td>
      <td>${citations || "—"}</td>
    `;
    tbody.appendChild(tr);
  }

  renderEvidenceList("#trustedSources", report.evidence?.trusted_sources || [], (e) => {
    const meta = [e.publisher, e.date, e.credibility].filter(Boolean).join(" • ");
    const thumb = e.thumbnail_url ? `<img src="${e.thumbnail_url}" alt="thumbnail" style="max-width:140px;border-radius:10px;border:1px solid #243058;margin-top:8px;" />` : "";
    return { title: e.title || e.url, url: e.url, meta, snippet: e.snippet, extraHtml: thumb };
  });

  renderEvidenceList("#webExtracts", report.evidence?.web_extracts || [], (e) => {
    const meta = [e.publisher, e.date, e.credibility].filter(Boolean).join(" • ");
    const thumb = e.thumbnail_url ? `<img src="${e.thumbnail_url}" alt="thumbnail" style="max-width:140px;border-radius:10px;border:1px solid #243058;margin-top:8px;" />` : "";
    return { title: e.title || e.url, url: e.url, meta, snippet: e.snippet, extraHtml: thumb };
  });

  renderEvidenceList("#imageMatches", report.evidence?.image_matches || [], (e) => {
    const meta = [e.publisher, e.date, e.credibility].filter(Boolean).join(" • ");
    const thumb = e.thumbnail_url ? `<img src="${e.thumbnail_url}" alt="thumbnail" style="max-width:120px;border-radius:10px;border:1px solid #243058;" />` : "";
    return { title: e.title || e.url, url: e.url, meta, extraHtml: thumb };
  });

  // Origin tracing
  const urls = report.origin_tracing?.most_likely_origin_urls || [];
  $("#originUrls").textContent = urls.length ? urls.join("\n") : "—";
  $("#earliest").textContent = report.origin_tracing?.earliest_appearance || "—";

  const timeline = report.origin_tracing?.timeline || [];
  const tl = $("#timeline");
  tl.innerHTML = "";
  if (!timeline.length) tl.appendChild(el("div", { class: "item", text: "—" }));
  for (const t of timeline) {
    const meta = [t.date, t.source].filter(Boolean).join(" • ");
    tl.appendChild(renderItem({ title: t.url || "timeline item", url: t.url, meta, snippet: t.context }));
  }

  // Limitations
  const lim = $("#limitations");
  lim.innerHTML = "";
  const items = report.limitations || [];
  if (!items.length) lim.appendChild(el("li", { text: "—" }));
  for (const it of items) lim.appendChild(el("li", { text: it }));
}

function renderEvidenceList(containerSel, items, mapper) {
  const container = $(containerSel);
  container.innerHTML = "";
  if (!items.length) {
    container.appendChild(el("div", { class: "item", text: "—" }));
    return;
  }
  for (const it of items.slice(0, 12)) {
    container.appendChild(renderItem(mapper(it)));
  }
}

function renderItem({ title, url, meta, snippet, extraHtml }) {
  const wrap = document.createElement("div");
  wrap.className = "item";

  const link = url ? `<a href="${url}" target="_blank" rel="noreferrer">${escapeHtml(title || url)}</a>` : `<div>${escapeHtml(title || "")}</div>`;
  wrap.innerHTML = `
    <div>${link}</div>
    <div class="small">${escapeHtml(meta || "")}</div>
    ${snippet ? `<div class="small" style="margin-top:6px;">${escapeHtml(snippet)}</div>` : ""}
    ${extraHtml || ""}
  `;
  return wrap;
}

function escapeHtml(s) {
  return (s || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

async function loadAudit() {
  if (!currentReportId) return setStatus("No report loaded yet.");
  setStatus("Loading audit...");
  const r = await fetch(`${API_BASE}/reports/${currentReportId}/audit`);
  if (!r.ok) throw new Error(await r.text());
  const data = await r.json();
  $("#audit").textContent = JSON.stringify(data, null, 2);
  setStatus("Audit loaded.");
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.querySelector(`.panel[data-panel='${btn.dataset.tab}']`).classList.add("active");
      setStatus("");
    });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  $("#analyzeTextBtn").addEventListener("click", () => uploadText().catch(e => setStatus(friendlyFetchError(e))));
  $("#analyzeImageBtn").addEventListener("click", () => uploadFile("image", "#imageFile").catch(e => setStatus(friendlyFetchError(e))));
  $("#analyzeAudioBtn").addEventListener("click", () => uploadFile("audio", "#audioFile").catch(e => setStatus(friendlyFetchError(e))));
  $("#loadAuditBtn").addEventListener("click", () => loadAudit().catch(e => setStatus(friendlyFetchError(e))));
});
