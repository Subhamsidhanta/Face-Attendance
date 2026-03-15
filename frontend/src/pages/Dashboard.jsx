import { useState } from "react";
import LiveFeed from "../components/LiveFeed";
import AlertPanel from "../components/AlertPanel";
import AttendanceLog from "../components/AttendanceLog";
import {
  startMonitoring,
  stopMonitoring,
  monitoringStatus,
} from "../services/api";
import { useEffect } from "react";

export default function Dashboard() {
  const [engineStatus, setEngineStatus] = useState({
    running: false,
    blinks: 0,
    blinkThreshold: 3,
    registeredNames: [],
  });

  useEffect(() => {
    const fetch = () =>
      monitoringStatus().then(setEngineStatus).catch(() => {});
    fetch();
    const id = setInterval(fetch, 3000);
    return () => clearInterval(id);
  }, []);

  const handleToggle = async () => {
    if (engineStatus.running) {
      await stopMonitoring();
    } else {
      await startMonitoring();
    }
    const s = await monitoringStatus();
    setEngineStatus(s);
  };

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Live Monitoring</h2>
          <p>Real-time face attendance with anti-spoofing verification</p>
        </div>
        <button
          className={`btn btn-lg ${engineStatus.running ? "btn-danger" : "btn-primary"}`}
          onClick={handleToggle}
        >
          {engineStatus.running ? "■ Stop Monitoring" : "▶ Start Monitoring"}
        </button>
      </div>

      <div className="dashboard-grid stagger-in">
        {/* Live Feed */}
        <div className="dashboard-feed">
          <LiveFeed />

          {/* Engine stats bar */}
          <div
            className="flex gap-4 mt-3"
            style={{ flexWrap: "wrap" }}
          >
            <div className="flex items-center gap-2">
              <span
                className={`status-dot ${engineStatus.running ? "online" : "offline"}`}
              />
              <span className="text-sm">
                {engineStatus.running ? "Engine Running" : "Engine Stopped"}
              </span>
            </div>
            <div className="text-sm text-muted">
              Blinks: {engineStatus.blinks}/{engineStatus.blinkThreshold}
            </div>
            <div className="text-sm text-muted">
              Models:{" "}
              {engineStatus.modelsLoaded ? (
                <span className="text-green">Loaded</span>
              ) : (
                <span className="text-red">Not loaded</span>
              )}
            </div>
            <div className="text-sm text-muted">
              Registered: {engineStatus.registeredNames?.length || 0} people
            </div>
          </div>
        </div>

        {/* Alert panel */}
        <div className="dashboard-alert">
          <AlertPanel />
        </div>

        {/* Engine status card */}
        <div className="dashboard-status">
          <div className="card">
            <div className="card-header">
              <h3>📊 System Status</h3>
            </div>
            <div className="card-body flex flex-col gap-3">
              <div className="flex justify-between">
                <span className="text-sm text-muted">Recognizer</span>
                <span className="text-sm">
                  {engineStatus.recognizerLoaded ? (
                    <span className="tag tag-green">Ready</span>
                  ) : (
                    <span className="tag tag-red">Not Loaded</span>
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted">Liveness Model</span>
                <span className="text-sm">
                  {engineStatus.livenessLoaded ? (
                    <span className="tag tag-green">Ready</span>
                  ) : (
                    <span className="tag tag-red">Not Loaded</span>
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted">Registered People</span>
                <span className="text-sm text-green">
                  {engineStatus.registeredNames?.length || 0}
                </span>
              </div>
              {engineStatus.registeredNames?.length > 0 && (
                <div className="flex gap-2" style={{ flexWrap: "wrap", marginTop: 4 }}>
                  {engineStatus.registeredNames.map((n) => (
                    <span key={n} className="tag tag-green">
                      {n}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Attendance log */}
        <div className="dashboard-log">
          <AttendanceLog />
        </div>
      </div>
    </div>
  );
}
