import { useState } from "react";
import { api } from "../api";

const EMPTY = { endpoint: "", method: "POST", request_schema: "", response_schema: "" };

function SchemaPreview({ reqRaw, resRaw }) {
  function tryParse(raw) { try { return JSON.parse(raw); } catch { return null; } }
  const req = tryParse(reqRaw);
  const res = tryParse(resRaw);
  if (!req && !res) return (
    <div className="preview-empty">
      Valid schema preview will appear here as you type.
    </div>
  );

  const scrollBox = {
    maxHeight: 180,
    overflowY: "auto",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--surface2)",
  };
  const innerPre = { margin: 0, border: "none", background: "transparent", borderRadius: 0 };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {req && (
        <div>
          <div className="schema-label">Request</div>
          <div style={scrollBox}><pre style={innerPre}>{JSON.stringify(req, null, 2)}</pre></div>
        </div>
      )}
      {res && (
        <div>
          <div className="schema-label">Response</div>
          <div style={scrollBox}><pre style={innerPre}>{JSON.stringify(res, null, 2)}</pre></div>
        </div>
      )}
    </div>
  );
}

export default function CreateContract({ onCreated }) {
  const [form, setForm] = useState(EMPTY);
  const [aiDesc, setAiDesc] = useState("");
  const [aiTarget, setAiTarget] = useState("request_schema");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  function set(field, value) { setForm((p) => ({ ...p, [field]: value })); }
  function parseSchema(raw) { try { return JSON.parse(raw); } catch { return null; } }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus(null);
    const rawReq = form.request_schema.trim();
    const rawRes = form.response_schema.trim();
    if (!rawRes) return setStatus({ ok: false, msg: "Response schema is required." });
    const reqSchema = rawReq === "" ? {} : parseSchema(rawReq);
    const resSchema = parseSchema(rawRes);
    if (reqSchema === null) return setStatus({ ok: false, msg: "Request schema is not valid JSON." });
    if (resSchema === null) return setStatus({ ok: false, msg: "Response schema is not valid JSON." });
    if (Object.keys(resSchema).length === 0) return setStatus({ ok: false, msg: "Response schema cannot be empty." });
    setLoading(true);
    const { ok, data } = await api.createContract({ endpoint: form.endpoint, method: form.method, request_schema: reqSchema, response_schema: resSchema });
    setLoading(false);
    if (ok) { setStatus({ ok: true, msg: "Contract created." }); setForm(EMPTY); onCreated(); }
    else setStatus({ ok: false, msg: data.error || "Failed to create contract." });
  }

  async function handleGenerateSchema() {
    if (!aiDesc.trim()) return;
    setAiLoading(true);
    const { ok, data } = await api.generateSchema(aiDesc);
    setAiLoading(false);
    if (ok && data.schema) set(aiTarget, JSON.stringify(data.schema, null, 2));
    else setStatus({ ok: false, msg: data.error || "AI generation failed." });
  }

  return (
    <>
      <div className="page-header">
        <div className="page-title">Create Contract</div>
        <div className="page-sub">Define request and response schemas for an endpoint</div>
      </div>

      <div className="create-grid" style={{ alignItems: "stretch" }}>
        {/* Form */}
        <div className="panel">
          <div className="panel-header"><span className="panel-dot" />Definition</div>
          <div className="panel-body">
            <form onSubmit={handleSubmit}>
              <div className="field">
                <label className="field-label">Endpoint</label>
                <input value={form.endpoint} onChange={(e) => set("endpoint", e.target.value)} placeholder="/api/users" required />
              </div>
              <div className="field">
                <label className="field-label">Method</label>
                <select value={form.method} onChange={(e) => set("method", e.target.value)}>
                  {["GET","POST","PUT","PATCH","DELETE"].map((m) => <option key={m}>{m}</option>)}
                </select>
              </div>
              <div className="field">
                <label className="field-label">Request Schema (JSON)</label>
                <textarea rows={4} value={form.request_schema} onChange={(e) => set("request_schema", e.target.value)}
                  placeholder='{"name": {"type": "string", "required": true}}' />
              </div>
              <div className="field">
                <label className="field-label">Response Schema (JSON)</label>
                <textarea rows={4} value={form.response_schema} onChange={(e) => set("response_schema", e.target.value)}
                  placeholder='{"id": {"type": "integer", "required": true}}' />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} disabled={loading}>
                {loading ? "Saving…" : "Create Contract"}
              </button>
              {status && <div className={`msg ${status.ok ? "msg-ok" : "msg-err"}`}>{status.msg}</div>}
            </form>
          </div>
        </div>

        {/* Preview */}
        <div className="panel" style={{ display: "flex", flexDirection: "column" }}>
          <div className="panel-header"><span className="panel-dot" style={{ background: "var(--muted)" }} />Preview</div>
          <div className="panel-body" style={{ flex: 1 }}>
            <SchemaPreview reqRaw={form.request_schema} resRaw={form.response_schema} />
          </div>
        </div>
      </div>

      {/* AI Generator */}
      <div className="ai-section">
        <div className="panel-header">
          <span className="panel-dot" style={{ background: "var(--warning)" }} />
          AI Schema Generator
          <span style={{ color: "var(--muted)", fontWeight: 400, marginLeft: 6, fontSize: 11, textTransform: "none", letterSpacing: 0 }}>
            — describe in plain English
          </span>
        </div>
        <div className="panel-body">
          <div className="ai-row">
            <div className="field">
              <label className="field-label">Description</label>
              <input value={aiDesc} onChange={(e) => setAiDesc(e.target.value)}
                placeholder="e.g. a user with name, age, and email" />
            </div>
            <div className="field" style={{ minWidth: 170 }}>
              <label className="field-label">Target</label>
              <select value={aiTarget} onChange={(e) => setAiTarget(e.target.value)}>
                <option value="request_schema">Request Schema</option>
                <option value="response_schema">Response Schema</option>
              </select>
            </div>
            <button className="btn btn-primary" onClick={handleGenerateSchema}
              disabled={aiLoading} style={{ marginTop: 20, flexShrink: 0 }}>
              {aiLoading ? "Generating…" : "Generate"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
