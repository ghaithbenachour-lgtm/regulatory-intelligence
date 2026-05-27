const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

export const api = {
  getJurisdictions: () => request("/api/jurisdictions"),
  getArticles: (params) => {
    const query = new URLSearchParams();
    (params.jurisdictions || []).forEach((j) => query.append("jurisdictions", j));
    (params.topics || []).forEach((t) => query.append("topics", t));
    if (params.dateFrom) query.set("date_from", params.dateFrom);
    if (params.dateTo) query.set("date_to", params.dateTo);
    query.set("page", params.page || 1);
    query.set("page_size", params.pageSize || 20);
    return request(`/api/articles?${query.toString()}`);
  },
  saveUser: (payload) =>
    request("/api/users", { method: "POST", body: JSON.stringify(payload) }),
  getUser: (email) => request(`/api/users/${encodeURIComponent(email)}`),
  previewDigest: (email) => request(`/api/digests/preview/${encodeURIComponent(email)}`),
  sendDigest: (email) =>
    request(`/api/digests/send/${encodeURIComponent(email)}`, { method: "POST" }),
  getDigestHistory: (email) =>
    request(`/api/digests/history/${encodeURIComponent(email)}`),
  getSourceHealth: () => request("/api/admin/health/sources"),
  getIngestionRuns: () => request("/api/admin/ingestion/runs"),
  triggerIngestion: () => request("/api/admin/ingestion/run", { method: "POST" }),
};
