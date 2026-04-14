import { useState, useEffect } from "react";
import ContractList from "./components/ContractList";
import CreateContract from "./components/CreateContract";
import LogViewer from "./components/LogViewer";
import { api } from "./api";
import "./App.css";

const NAV = [
  { id: "Contracts", icon: "◈", label: "Contracts" },
  { id: "Create",    icon: "+", label: "Create"    },
  { id: "Logs",      icon: "≡", label: "Logs"      },
];

export default function App() {
  const [tab, setTab] = useState("Contracts");
  const [refresh, setRefresh] = useState(0);
  const [theme, setTheme] = useState(() =>
    localStorage.getItem("theme") || "dark"
  );
  const [contractCount, setContractCount] = useState(0);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    api.getContracts().then(({ ok, data }) => {
      if (ok) setContractCount(data.length);
    });
  }, [refresh]);

  function handleCreated() {
    setRefresh((r) => r + 1);
    setTab("Contracts");
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-title">Contract Guardian</div>
          <div className="sidebar-brand-sub">runtime enforcement</div>
        </div>

        <nav className="sidebar-nav">
          {NAV.map((item) => (
            <div
              key={item.id}
              className={`sidebar-item${tab === item.id ? " active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <span className="sidebar-item-icon">{item.icon}</span>
              {item.label}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="sidebar-footer-text">flask · sqlite</span>
          <div className="theme-toggle">
            <button
              className={`theme-toggle-btn${theme === "light" ? " active" : ""}`}
              onClick={() => setTheme("light")}
              title="Light mode"
            >☀</button>
            <button
              className={`theme-toggle-btn${theme === "dark" ? " active" : ""}`}
              onClick={() => setTheme("dark")}
              title="Dark mode"
            >◑</button>
          </div>
        </div>
      </aside>

      <div className="main-wrap">
        {/* System header */}
        <div className="sys-header">
          <div className="sys-header-left">
            <div>
              <div className="sys-header-title">API Contract Guardian</div>
              <div className="sys-header-sub">Runtime Enforcement System</div>
            </div>
          </div>
          <div className="sys-header-right">
            <div className="stat-chip"><span>{contractCount}</span> contract{contractCount !== 1 ? "s" : ""} enforced</div>
            <div className="status-pill">
              <span className="status-dot" />
              Active
            </div>
          </div>
        </div>

        <main className="main">
          {tab === "Contracts" && <ContractList refresh={refresh} />}
          {tab === "Create"    && <CreateContract onCreated={handleCreated} />}
          {tab === "Logs"      && <LogViewer />}
        </main>
      </div>
    </div>
  );
}
