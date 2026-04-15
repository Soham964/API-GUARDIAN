const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

async function request(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

export const api = {
  getContracts: () => request("GET", "/contracts"),
  createContract: (body) => request("POST", "/contracts", body),
  deleteContract: (id) => request("DELETE", `/contracts/${id}`),
  getLogs: () => request("GET", "/logs"),
  testValidate: (body) => request("POST", "/test/validate", body),
  generateSchema: (description) =>
    request("POST", "/ai/generate-schema", { description }),
  explainError: (error_message) =>
    request("POST", "/ai/explain-error", { error_message }),
};
