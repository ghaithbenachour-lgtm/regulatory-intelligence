import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const TOPICS = ["crypto", "tech", "ai"];
const SAVED_VIEWS_KEY = "regulatory_saved_views";

function loadSavedViews() {
  try {
    return JSON.parse(localStorage.getItem(SAVED_VIEWS_KEY) || "[]");
  } catch {
    return [];
  }
}

function FeedPanel({ jurisdictions, selectedJurisdictions, selectedTopics, dateFrom, dateTo }) {
  const [articles, setArticles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    api
      .getArticles({
        jurisdictions: selectedJurisdictions,
        topics: selectedTopics,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      })
      .then((data) => {
        setArticles(data.items);
        setTotal(data.total);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedJurisdictions, selectedTopics, dateFrom, dateTo]);

  const jurisdictionMap = useMemo(
    () => Object.fromEntries(jurisdictions.map((j) => [j.code, j.name])),
    [jurisdictions]
  );

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Regulatory Feed</h2>
        <span className="badge">{total} updates</span>
      </div>
      {loading && <p className="muted">Loading official updates...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && articles.length === 0 && (
        <p className="muted">No articles match your filters yet. Try running ingestion from Admin.</p>
      )}
      <div className="article-list">
        {articles.map((article) => (
          <article key={article.id} className="article-card">
            <div className="article-meta">
              {(article.tags || []).map((tag) => (
                <span key={`${article.id}-${tag.topic}`} className="tag">
                  {jurisdictionMap[tag.jurisdiction] || tag.jurisdiction} · {tag.topic}
                </span>
              ))}
            </div>
            <h3>
              <a href={article.canonical_url} target="_blank" rel="noreferrer">
                {article.title}
              </a>
            </h3>
            {article.summary && <p>{article.summary.slice(0, 280)}{article.summary.length > 280 ? "..." : ""}</p>}
            <footer>
              <span>{article.agency || article.source_name}</span>
              {article.published_at && (
                <span>{new Date(article.published_at).toLocaleDateString()}</span>
              )}
            </footer>
          </article>
        ))}
      </div>
    </section>
  );
}

function PreferencesPanel({
  jurisdictions,
  email,
  setEmail,
  selectedJurisdictions,
  setSelectedJurisdictions,
  selectedTopics,
  setSelectedTopics,
}) {
  const [name, setName] = useState("");
  const [status, setStatus] = useState("");
  const [savedViews, setSavedViews] = useState(loadSavedViews);

  const toggleJurisdiction = (code) => {
    setSelectedJurisdictions((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const toggleTopic = (topic) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const savePreferences = async () => {
    setStatus("Saving...");
    try {
      const preferences = [];
      for (const jurisdiction of selectedJurisdictions) {
        for (const topic of selectedTopics) {
          preferences.push({ jurisdiction, topic });
        }
      }
      await api.saveUser({ email, name, preferences });
      setStatus("Preferences saved.");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const saveCurrentView = () => {
    const label = prompt("Name this saved view (e.g. UAE + AI):");
    if (!label) return;
    const view = {
      id: Date.now(),
      label,
      jurisdictions: selectedJurisdictions,
      topics: selectedTopics,
    };
    const next = [...savedViews, view];
    setSavedViews(next);
    localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(next));
  };

  const applyView = (view) => {
    setSelectedJurisdictions(view.jurisdictions);
    setSelectedTopics(view.topics);
  };

  return (
    <section className="panel sidebar">
      <h2>Your Preferences</h2>
      <label>
        Email
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
      </label>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>

      <h3>Jurisdictions</h3>
      <div className="chip-grid">
        {jurisdictions.map((j) => (
          <button
            key={j.code}
            type="button"
            className={`chip ${selectedJurisdictions.includes(j.code) ? "active" : ""}`}
            onClick={() => toggleJurisdiction(j.code)}
          >
            {j.name}
          </button>
        ))}
      </div>

      <h3>Topics</h3>
      <div className="chip-grid">
        {TOPICS.map((topic) => (
          <button
            key={topic}
            type="button"
            className={`chip ${selectedTopics.includes(topic) ? "active" : ""}`}
            onClick={() => toggleTopic(topic)}
          >
            {topic.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="actions">
        <button type="button" onClick={savePreferences}>Save for daily digest</button>
        <button type="button" className="secondary" onClick={saveCurrentView}>Save view</button>
      </div>
      {status && <p className="muted">{status}</p>}

      {savedViews.length > 0 && (
        <>
          <h3>Saved Views</h3>
          <div className="saved-views">
            {savedViews.map((view) => (
              <button key={view.id} type="button" className="secondary" onClick={() => applyView(view)}>
                {view.label}
              </button>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function DigestPanel({ email }) {
  const [preview, setPreview] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("");

  const loadPreview = async () => {
    setStatus("Loading preview...");
    try {
      const data = await api.previewDigest(email);
      setPreview(data);
      setStatus("");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const sendDigest = async () => {
    setStatus("Sending digest...");
    try {
      await api.sendDigest(email);
      setStatus("Digest sent.");
      const hist = await api.getDigestHistory(email);
      setHistory(hist);
    } catch (err) {
      setStatus(err.message);
    }
  };

  useEffect(() => {
    api.getDigestHistory(email).then(setHistory).catch(() => setHistory([]));
  }, [email]);

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Daily Digest</h2>
        <div className="actions inline">
          <button type="button" className="secondary" onClick={loadPreview}>Preview</button>
          <button type="button" onClick={sendDigest}>Send now</button>
        </div>
      </div>
      {status && <p className="muted">{status}</p>}
      {preview && (
        <div className="digest-preview">
          <h3>{preview.subject}</h3>
          <p className="badge">{preview.item_count} items</p>
          <div dangerouslySetInnerHTML={{ __html: preview.body_html }} />
        </div>
      )}
      {history.length > 0 && (
        <>
          <h3>History</h3>
          <ul className="history-list">
            {history.map((item) => (
              <li key={item.id}>
                {item.digest_date} — {item.item_count} items — {item.status}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function AdminPanel() {
  const [sources, setSources] = useState([]);
  const [runs, setRuns] = useState([]);
  const [status, setStatus] = useState("");

  const refresh = async () => {
    const [health, ingestionRuns] = await Promise.all([
      api.getSourceHealth(),
      api.getIngestionRuns(),
    ]);
    setSources(health);
    setRuns(ingestionRuns);
  };

  useEffect(() => {
    refresh().catch((err) => setStatus(err.message));
  }, []);

  const triggerIngestion = async () => {
    setStatus("Running ingestion...");
    try {
      const result = await api.triggerIngestion();
      setStatus(`Ingestion done: ${result.articles_new} new, ${result.articles_skipped} skipped`);
      await refresh();
    } catch (err) {
      setStatus(err.message);
    }
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Admin & Observability</h2>
        <button type="button" onClick={triggerIngestion}>Run ingestion</button>
      </div>
      {status && <p className="muted">{status}</p>}

      <h3>Source Health</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Jurisdiction</th>
              <th>Status</th>
              <th>Last Success</th>
              <th>Failures</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id} className={source.healthy ? "ok" : source.stale ? "stale" : "warn"}>
                <td>{source.name}</td>
                <td>{source.jurisdiction}</td>
                <td>{source.healthy ? "Healthy" : source.stale ? "Stale" : "Degraded"}</td>
                <td>{source.last_success_at ? new Date(source.last_success_at).toLocaleString() : "—"}</td>
                <td>{source.consecutive_failures}</td>
                <td className="error-cell">{source.last_error || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3>Recent Ingestion Runs</h3>
      <ul className="history-list">
        {runs.map((run) => (
          <li key={run.id}>
            #{run.id} {run.status} — new {run.articles_new}, skipped {run.articles_skipped}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function App() {
  const [tab, setTab] = useState("feed");
  const [jurisdictions, setJurisdictions] = useState([]);
  const [email, setEmail] = useState(localStorage.getItem("regulatory_email") || "demo@example.com");
  const [selectedJurisdictions, setSelectedJurisdictions] = useState(["US", "SG", "AE"]);
  const [selectedTopics, setSelectedTopics] = useState(["crypto", "ai"]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useEffect(() => {
    localStorage.setItem("regulatory_email", email);
  }, [email]);

  useEffect(() => {
    api.getJurisdictions().then(setJurisdictions).catch(console.error);
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Official sources only</p>
          <h1>Regulatory Intelligence</h1>
          <p>Daily crypto, tech, and AI regulation updates across your chosen jurisdictions.</p>
        </div>
        <nav className="tabs">
          {["feed", "digest", "admin"].map((key) => (
            <button
              key={key}
              type="button"
              className={tab === key ? "active" : ""}
              onClick={() => setTab(key)}
            >
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </button>
          ))}
        </nav>
      </header>

      <main className="layout">
        <PreferencesPanel
          jurisdictions={jurisdictions}
          email={email}
          setEmail={setEmail}
          selectedJurisdictions={selectedJurisdictions}
          setSelectedJurisdictions={setSelectedJurisdictions}
          selectedTopics={selectedTopics}
          setSelectedTopics={setSelectedTopics}
        />

        <div className="main-column">
          {tab === "feed" && (
            <>
              <section className="panel filters">
                <h2>Filters</h2>
                <div className="filter-row">
                  <label>
                    From
                    <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </label>
                  <label>
                    To
                    <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </label>
                </div>
              </section>
              <FeedPanel
                jurisdictions={jurisdictions}
                selectedJurisdictions={selectedJurisdictions}
                selectedTopics={selectedTopics}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            </>
          )}
          {tab === "digest" && <DigestPanel email={email} />}
          {tab === "admin" && <AdminPanel />}
        </div>
      </main>
    </div>
  );
}
