import { useEffect, useState } from "react";
import { api } from "../api";

export default function LogViewer() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getLogs().then(({ ok, data }) => {
      if (ok) setLogs(data);
      else setError("Failed to load logs.");
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <div className="page-title">Validation Logs</div>
        <div className="page-sub">{logs.length} violation{logs.length !== 1 ? "s" : ""} recorded</div>
      </div>

      {error && <div className="msg msg-err">{error}</div>}

      <div className="table-wrap">
        {logs.length === 0 ? (
          <div className="empty-state">No violations recorded yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 155 }}>Timestamp</th>
                <th style={{ width: 75 }}>Method</th>
                <th>Endpoint</th>
                <th style={{ width: 105 }}>Direction</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className={`log-row-${log.direction}`}>
                  <td style={{ color: "var(--muted)", fontFamily: "var(--mono)", fontSize: 11 }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td><span className={`badge badge-${log.method}`}>{log.method}</span></td>
                  <td><code>{log.endpoint}</code></td>
                  <td>
                    <span className={`badge badge-${log.direction}`}>
                      {log.direction === "request" ? "↑ REQUEST" : "↓ RESPONSE"}
                    </span>
                  </td>
                  <td style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--text2)" }}>
                    {log.error_message}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
