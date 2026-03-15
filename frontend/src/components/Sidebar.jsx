import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { healthCheck } from "../services/api";

export default function Sidebar() {
  const [health, setHealth] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const check = () =>
      healthCheck()
        .then(setHealth)
        .catch(() => setHealth(null));
    check();
    const id = setInterval(check, 5000);
    return () => clearInterval(id);
  }, []);

  const links = [
    { to: "/", icon: "◉", label: "Dashboard" },
    { to: "/register", icon: "⊕", label: "Register Face" },
    { to: "/unknown", icon: "⚠", label: "Unknown Gallery" },
    { to: "/settings", icon: "⚙", label: "Settings" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>
          <span className="icon">👁</span>
          FaceGuard
        </h1>
        <p>Attendance System</p>
      </div>

      <nav className="sidebar-nav">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <span className="link-icon">{l.icon}</span>
            <span>{l.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span
            className={`status-dot ${health?.camera ? "online" : "offline"}`}
          />
          <span>{health?.camera ? "Camera Online" : "Camera Offline"}</span>
        </div>
        <div className="sidebar-status" style={{ marginTop: 6 }}>
          <span
            className={`status-dot ${health?.engine ? "online" : "offline"}`}
          />
          <span>{health?.engine ? "Monitoring Active" : "Monitoring Off"}</span>
        </div>
      </div>
    </aside>
  );
}
