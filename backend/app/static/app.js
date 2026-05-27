const TOPICS = ["crypto", "tech", "ai"];
const state = {
  email: localStorage.getItem("regulatory_email") || "",
  jurisdictions: [],
  selectedJurisdictions: JSON.parse(localStorage.getItem("regulatory_jurisdictions") || '["US","SG","HK","AE","EU"]'),
  selectedTopics: JSON.parse(localStorage.getItem("regulatory_topics") || '["crypto","tech","ai"]'),
  dateFrom: "",
  dateTo: "",
  tab: "feed",
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text() || res.statusText);
  return res.json();
}

function persistFilters() {
  localStorage.setItem("regulatory_jurisdictions", JSON.stringify(state.selectedJurisdictions));
  localStorage.setItem("regulatory_topics", JSON.stringify(state.selectedTopics));
  localStorage.setItem("regulatory_email", state.email);
}

function setStatus(msg, isError = false) {
  const el = document.getElementById("status");
  if (!el) return;
  el.textContent = msg;
  el.className = isError ? "error" : "muted";
}

function renderPrefs() {
  const el = document.getElementById("prefs");
  el.innerHTML = `
    <h2>Your Watchlist</h2>
    <p class="muted small">Choose jurisdictions and topics. Filters apply instantly to the feed.</p>
    <h3>Jurisdictions</h3>
    <div class="chip-grid" id="jurisdiction-chips"></div>
    <h3>Topics</h3>
    <div class="chip-grid" id="topic-chips"></div>
    <div class="actions">
      <button class="primary" id="save-prefs">Save for email digest</button>
    </div>
    <p id="status" class="muted"></p>
  `;

  const jEl = document.getElementById("jurisdiction-chips");
  state.jurisdictions.forEach((j) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `chip ${state.selectedJurisdictions.includes(j.code) ? "active" : ""}`;
    btn.textContent = j.name;
    btn.onclick = () => {
      state.selectedJurisdictions = state.selectedJurisdictions.includes(j.code)
        ? state.selectedJurisdictions.filter((c) => c !== j.code)
        : [...state.selectedJurisdictions, j.code];
      persistFilters();
      renderPrefs();
      loadFeed();
    };
    jEl.appendChild(btn);
  });

  const tEl = document.getElementById("topic-chips");
  TOPICS.forEach((topic) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `chip ${state.selectedTopics.includes(topic) ? "active" : ""}`;
    btn.textContent = topic.toUpperCase();
    btn.onclick = () => {
      state.selectedTopics = state.selectedTopics.includes(topic)
        ? state.selectedTopics.filter((t) => t !== topic)
        : [...state.selectedTopics, topic];
      persistFilters();
      renderPrefs();
      loadFeed();
    };
    tEl.appendChild(btn);
  });

  document.getElementById("save-prefs").onclick = savePrefs;
}

function renderFilters() {
  document.getElementById("filters").innerHTML = `
    <div class="panel-header">
      <h2>Filters</h2>
      <span class="badge" id="feed-count">—</span>
    </div>
    <div class="filter-row">
      <label>From<input type="date" id="date-from" value="${state.dateFrom}" /></label>
      <label>To<input type="date" id="date-to" value="${state.dateTo}" /></label>
      <button type="button" class="secondary" id="clear-dates">Clear dates</button>
    </div>
  `;
  document.getElementById("date-from").onchange = (e) => { state.dateFrom = e.target.value; loadFeed(); };
  document.getElementById("date-to").onchange = (e) => { state.dateTo = e.target.value; loadFeed(); };
  document.getElementById("clear-dates").onclick = () => {
    state.dateFrom = "";
    state.dateTo = "";
    renderFilters();
    loadFeed();
  };
}

function renderDigestPanel() {
  document.getElementById("digest-panel").innerHTML = `
    <div class="panel-header">
      <h2>Daily Email Digest</h2>
    </div>
    <p class="muted">Get a daily email with official updates matching your watchlist.</p>
    <label>Your email
      <input id="digest-email" type="email" placeholder="you@company.com" value="${state.email}" />
    </label>
    <div class="actions">
      <button type="button" class="primary" id="save-digest-email">Save email & preferences</button>
      <button type="button" class="secondary" id="preview-digest">Preview today's digest</button>
    </div>
    <div id="digest-preview" class="digest-preview hidden"></div>
    <p id="digest-status" class="muted"></p>
  `;
  document.getElementById("digest-email").onchange = (e) => {
    state.email = e.target.value.trim();
    persistFilters();
  };
  document.getElementById("save-digest-email").onclick = savePrefs;
  document.getElementById("preview-digest").onclick = previewDigest;
}

async function savePrefs() {
  const emailInput = document.getElementById("digest-email") || document.getElementById("email");
  if (emailInput) state.email = emailInput.value.trim();
  if (!state.email) {
    setStatus("Enter your email to save digest preferences.", true);
    return;
  }
  persistFilters();
  const preferences = [];
  for (const jurisdiction of state.selectedJurisdictions) {
    for (const topic of state.selectedTopics) preferences.push({ jurisdiction, topic });
  }
  if (!preferences.length) {
    setStatus("Select at least one jurisdiction and topic.", true);
    return;
  }
  setStatus("Saving...");
  await api("/api/users", {
    method: "POST",
    body: JSON.stringify({ email: state.email, name: "Subscriber", preferences }),
  });
  setStatus("Saved. You'll receive digests when email is configured on the server.");
  const digestStatus = document.getElementById("digest-status");
  if (digestStatus) digestStatus.textContent = "Preferences saved.";
}

async function previewDigest() {
  if (!state.email) {
    const digestStatus = document.getElementById("digest-status");
    if (digestStatus) digestStatus.textContent = "Enter and save your email first.";
    return;
  }
  const data = await api(`/api/digests/preview/${encodeURIComponent(state.email)}`);
  const box = document.getElementById("digest-preview");
  box.classList.remove("hidden");
  box.innerHTML = `<h3>${data.subject}</h3><p class="badge">${data.item_count} items</p>${data.body_html}`;
  const digestStatus = document.getElementById("digest-status");
  if (digestStatus) digestStatus.textContent = `Preview ready — ${data.item_count} updates in the last 24h.`;
}

async function loadFeed() {
  const params = new URLSearchParams();
  state.selectedJurisdictions.forEach((j) => params.append("jurisdictions", j));
  state.selectedTopics.forEach((t) => params.append("topics", t));
  if (state.dateFrom) params.set("date_from", `${state.dateFrom}T00:00:00`);
  if (state.dateTo) params.set("date_to", `${state.dateTo}T23:59:59`);
  params.set("page_size", "30");

  const panel = document.getElementById("feed-panel");
  panel.innerHTML = `<p class="muted">Loading official updates...</p>`;

  try {
    const data = await api(`/api/articles?${params}`);
    const countEl = document.getElementById("feed-count");
    if (countEl) countEl.textContent = `${data.total} updates`;

    if (!data.items.length) {
      panel.innerHTML = `<p class="muted">No updates match your filters yet. Check back after the next ingestion cycle.</p>`;
      return;
    }

    panel.innerHTML = `<div class="article-list"></div>`;
    const list = panel.querySelector(".article-list");
    const jMap = Object.fromEntries(state.jurisdictions.map((j) => [j.code, j.name]));

    data.items.forEach((article) => {
      const card = document.createElement("article");
      card.className = "article-card";
      const tags = (article.tags || [])
        .map((t) => `<span class="tag">${jMap[t.jurisdiction] || t.jurisdiction} · ${t.topic}</span>`)
        .join("");
      const date = article.published_at
        ? new Date(article.published_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
        : "";
      card.innerHTML = `
        <div class="article-meta">${tags}</div>
        <h3><a href="${article.canonical_url}" target="_blank" rel="noopener noreferrer">${article.title}</a></h3>
        ${article.summary ? `<p>${article.summary.slice(0, 260)}${article.summary.length > 260 ? "…" : ""}</p>` : ""}
        <footer><span>${article.agency || article.source_name || "Official source"}</span><span>${date}</span></footer>
      `;
      list.appendChild(card);
    });
  } catch (err) {
    panel.innerHTML = `<p class="error">Could not load feed: ${err.message}</p>`;
  }
}

function setupTabs() {
  document.querySelectorAll("#tabs button").forEach((btn) => {
    btn.onclick = () => {
      state.tab = btn.dataset.tab;
      document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b === btn));
      document.getElementById("feed-panel").classList.toggle("hidden", state.tab !== "feed");
      document.getElementById("digest-panel").classList.toggle("hidden", state.tab !== "digest");
      document.getElementById("filters").classList.toggle("hidden", state.tab !== "feed");
      if (state.tab === "digest") renderDigestPanel();
    };
  });
}

async function init() {
  state.jurisdictions = await api("/api/jurisdictions");
  renderPrefs();
  renderFilters();
  renderDigestPanel();
  setupTabs();
  await loadFeed();
}

init().catch((err) => {
  const panel = document.getElementById("feed-panel");
  if (panel) panel.innerHTML = `<p class="error">Failed to start: ${err.message}</p>`;
});
