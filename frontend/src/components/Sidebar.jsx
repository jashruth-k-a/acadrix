import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { path: "/dashboard", icon: "📁", label: "Documents" },
  { path: "/query",     icon: "💬", label: "Ask"       },
  { path: "/history",   icon: "🕓", label: "History"   },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src="/acadrix-logo.svg" alt="Acadrix" className="logo-full"
          onError={(e) => {
            // Fallback if SVG not found
            e.currentTarget.style.display = "none";
            e.currentTarget.nextSibling.style.display = "flex";
          }}
        />
        <span className="logo-fallback" style={{ display: "none" }}>
          <span className="logo-icon">⬡</span>
          <span className="logo-text">Acadrix</span>
        </span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ path, icon, label }) => (
          <button
            key={path}
            className={`nav-item ${pathname === path ? "active" : ""}`}
            onClick={() => navigate(path)}
          >
            <span className="nav-icon">{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">
            {user?.name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="user-details">
            <p className="user-name">{user?.name}</p>
            <p className="user-email">{user?.email}</p>
          </div>
        </div>
        <button className="btn-logout" onClick={logout}>Sign out</button>
      </div>
    </aside>
  );
}
