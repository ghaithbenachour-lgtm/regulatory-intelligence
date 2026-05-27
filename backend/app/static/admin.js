async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text() || res.statusText);
  return res.json();
}

function setStatus(msg) {
  const el = document.getElementById("admin-status");
  if (el) el.textContent = msg;
}

async function loadAdmin() {
  const admin = document.getElementById("admin");
  admin.innerHTML = `
    <div class="panel-header">
      <h2>Source Health</h2>
      <button type="button" class="primary" id="run-ingest">Run ingestion now</button>
    </div>
    <p id="admin-status" class="muted"></p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Source</th><th>Jurisdiction</th><th>Status</th><th>Last success</th><th>Failures</th><th>Error</th></tr>
        </thead>
        <tbody id="source-rows"></tbody>
      </table>
    </div>
    <h3>Recent ingestion runs</h3>
    <ul class="history-list" id="run-rows"></ul>
  `;

  document.getElementById("run-ingest").onclick = async () => {
    setStatus("Running ingestion...");
    const result = await api("/api/admin/ingestion/run", { method: "POST" });
    setStatus(`Done — ${result.articles_new} new, ${result.articles_skipped} skipped`);
    await refresh();
  };

  await refresh();
}

async function refresh() {
  const [sources, runs] = await Promise.all([
    api("/api/admin/health/sources"),
    api("/api/admin/ingestion/runs"),
  ]);

  const tbody = document.getElementById("source-rows");
  tbody.innerHTML = "";
  sources.forEach((s) => {
    const tr = document.createElement("tr");
    tr.className = s.healthy ? "ok" : s.stale ? "stale" : "warn";
    tr.innerHTML = `
      <td>${s.name}</td>
      <td>${s.jurisdiction}</td>
      <td>${s.healthy ? "Healthy" : s.stale ? "Stale" : "Degraded"}</td>
      <td>${s.last_success_at ? new Date(s.last_success_at).toLocaleString() : "—"}</td>
      <td>${s.consecutive_failures}</td>
      <td class="error-cell">${s.last_error || "—"}</td>
    `;
    tbody.appendChild(tr);
  });

  const runList = document.getElementById("run-rows");
  runList.innerHTML = runs
    .map((r) => `<li>#${r.id} ${r.status} — ${r.articles_new} new, ${r.articles_skipped} skipped</li>`)
    .join("");
}

loadAdmin().catch((err) => {
  document.getElementById("admin").innerHTML = `<p class="error">${err.message}</p>`;
});
