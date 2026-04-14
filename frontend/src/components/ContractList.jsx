import { useEffect, useState } from "react";
import { api } from "../api";

function TestDrawer({ contract, onClose }) {
  const [payload, setPayload] = useState("");
  const [direction, setDirection] = useState("request");
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => { requestAnimationFrame(() => setOpen(true)); }, []);

  function handleClose() {
    setOpen(false);
    setTimeout(onClose, 200);
  }

  async function handleTest() {
    setResult(null);
    setExplanation("");
    let parsed;
    try { parsed = JSON.parse(payload || "{}"); }
    catch { setResult({ valid: false, errors: ["Payload is not valid JSON."] }); return; }
    setLoading(true);
    const { data } = await api.testValidate({ endpoint: contract.endpoint, method: contract.method, payload: parsed, direction });
    setLoading(false);
    setResult(data);
  }

  async function handleExplain(error) {
    setLoading(true);
    const { data } = await api.explainError(error);
    setLoading(false);
    setExplanation(data.explanation || error);
  }

  return (
    <>
      <div className="drawer-overlay" onClick={handleClose} />
      <div className={`drawer${open ? " open" : ""}`}>
        <div className="drawer-header">
          <div>
            <div className="drawer-title">Validate Payload</div>
            <div className="drawer-subtitle">{contract.method} {contract.endpoint}</div>
          </div>
          <button className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 12 }} onClick={handleClose}>✕</button>
        </div>

        <div className="drawer-body">
          <div style={{ marginBottom: 14 }}>
            <div className="field-label">Direction</div>
            <div className="toggle-group">
              <button className={`toggle-btn${direction === "request" ? " active" : ""}`}
                onClick={() => { setDirection("request"); setResult(null); setExplanation(""); }}>
                Request
              </button>
              <button className={`toggle-btn${direction === "response" ? " active" : ""}`}
                onClick={() => { setDirection("response"); setResult(null); setExplanation(""); }}>
                Response
              </button>
            </div>
          </div>

          <div className="field">
            <label className="field-label">Payload (JSON)</label>
            <textarea value={payload} onChange={(e) => setPayload(e.target.value)}
              placeholder='{"name": "Alice", "age": 30}' rows={8} />
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}
            onClick={handleTest} disabled={loading}>
            {loading ? "Validating…" : "Validate"}
          </button>

          <details className="schema-details">
            <summary>View schemas</summary>
            <div className="schema-label">Request</div>
            <pre>{JSON.stringify(contract.request_schema, null, 2)}</pre>
            <div className="schema-label">Response</div>
            <pre>{JSON.stringify(contract.response_schema, null, 2)}</pre>
          </details>
        </div>

        <div className="drawer-footer">
          {result && (
            <>
              <div className={`status-bar ${result.valid ? "valid" : "invalid"}`}>
                {result.valid ? "✓ Valid" : "✗ Invalid"}
              </div>
              {!result.valid && result.errors?.length > 0 && (
                <div className="error-list">
                  <ul>
                    {result.errors.map((e, i) => (
                      <li key={i}>
                        <span style={{ flex: 1 }}>{e}</span>
                        <button className="btn-link" onClick={() => handleExplain(e)}>explain</button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {!result.valid && (
                <div style={{ padding: "10px 20px", borderTop: "1px solid var(--border)" }}>
                  <button className="btn btn-ghost" style={{ fontSize: 12, padding: "5px 10px" }}
                    onClick={() => result.errors?.length && handleExplain(result.errors[0])}
                    disabled={loading}>
                    Explain with AI
                  </button>
                </div>
              )}
              {explanation && (
                <div className="ai-explanation">
                  <strong>AI Explanation</strong>
                  {explanation}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default function ContractList({ refresh }) {
  const [contracts, setContracts] = useState([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.getContracts().then(({ ok, data }) => {
      if (ok) setContracts(data);
      else setError("Failed to load contracts.");
    });
  }, [refresh]);

  async function handleDelete(id) {
    const { ok } = await api.deleteContract(id);
    if (ok) setContracts((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <>
      <div className="page-header">
        <div className="page-title">Contracts</div>
        <div className="page-sub">{contracts.length} endpoint{contracts.length !== 1 ? "s" : ""} registered</div>
      </div>

      {error && <div className="msg msg-err">{error}</div>}

      <div className="table-wrap">
        {contracts.length === 0 ? (
          <div className="empty-state">No contracts yet. Create one to get started.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 80 }}>Method</th>
                <th>Endpoint</th>
                <th style={{ width: 160 }}>Created</th>
                <th style={{ width: 130 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.id}>
                  <td><span className={`badge badge-${c.method}`}>{c.method}</span></td>
                  <td><code>{c.endpoint}</code></td>
                  <td style={{ color: "var(--muted)", fontFamily: "var(--mono)", fontSize: 11 }}>
                    {new Date(c.created_at).toLocaleString()}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                      <span className="active-badge">● active</span>
                      <button className="btn btn-ghost" style={{ padding: "4px 10px", fontSize: 12 }}
                        onClick={() => setSelected(c)}>Test</button>
                      <button className="btn btn-ghost-danger" style={{ padding: "4px 10px", fontSize: 12 }}
                        onClick={() => handleDelete(c.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && <TestDrawer contract={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
