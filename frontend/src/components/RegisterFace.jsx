import { useState, useEffect, useRef } from "react";
import {
  startRegistration,
  stopRegistration,
  registrationStatus,
  listRegistered,
} from "../services/api";
import LiveFeed from "./LiveFeed";
import TrainModel from "./TrainModel";

export default function RegisterFace() {
  const [name, setName] = useState("");
  const [limit, setLimit] = useState(250);
  const [status, setStatus] = useState({ capturing: false, count: 0, limit: 250 });
  const [people, setPeople] = useState([]);
  const pollRef = useRef(null);

  // Fetch registered people on mount
  useEffect(() => {
    listRegistered().then(setPeople).catch(() => {});
  }, [status.capturing]);

  // Poll status while capturing
  useEffect(() => {
    if (status.capturing) {
      pollRef.current = setInterval(() => {
        registrationStatus().then((s) => {
          setStatus(s);
          if (!s.capturing) clearInterval(pollRef.current);
        });
      }, 500);
    }
    return () => clearInterval(pollRef.current);
  }, [status.capturing]);

  const handleStart = async () => {
    if (!name.trim()) return;
    const res = await startRegistration(name.trim(), limit);
    if (res.ok) {
      setStatus({ capturing: true, count: 0, limit, name: name.trim() });
    }
  };

  const handleStop = async () => {
    await stopRegistration();
    setStatus((s) => ({ ...s, capturing: false }));
    listRegistered().then(setPeople).catch(() => {});
  };

  const pct = status.limit > 0 ? (status.count / status.limit) * 100 : 0;

  return (
    <div>
      <div className="page-header">
        <h2>Register New Face</h2>
        <p>Capture face images for recognition training</p>
      </div>

      <div className="grid-2">
        {/* Left — feed + form */}
        <div className="flex flex-col gap-5">
          <LiveFeed />

          <div className="card">
            <div className="card-header">
              <h3>⊕ Registration</h3>
              {status.capturing && (
                <span className="tag tag-amber">Capturing…</span>
              )}
            </div>
            <div className="card-body flex flex-col gap-4">
              <div className="form-group">
                <label className="form-label">Person Name</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="e.g. John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={status.capturing}
                />
              </div>

              <div className="range-wrapper">
                <div className="range-header">
                  <span className="form-label">Images to capture</span>
                  <span className="range-value">{limit}</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={500}
                  step={10}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  disabled={status.capturing}
                />
              </div>

              {status.capturing && (
                <div>
                  <div className="flex justify-between text-sm mb-4" style={{ marginBottom: 6 }}>
                    <span>
                      Progress: {status.count} / {status.limit}
                    </span>
                    <span className="text-green">{Math.round(pct)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                {!status.capturing ? (
                  <button
                    className="btn btn-primary btn-lg"
                    onClick={handleStart}
                    disabled={!name.trim()}
                  >
                    ▶ Start Capture
                  </button>
                ) : (
                  <button className="btn btn-danger btn-lg" onClick={handleStop}>
                    ■ Stop
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right — registered people + training */}
        <div className="flex flex-col gap-5">
          <div className="card">
            <div className="card-header">
              <h3>👥 Registered People</h3>
              <span className="tag tag-green">{people.length}</span>
            </div>
            <div
              className="card-body"
              style={{ maxHeight: 300, overflowY: "auto" }}
            >
              {people.length === 0 ? (
                <div className="empty-state" style={{ padding: "24px 16px" }}>
                  <span className="empty-icon">👤</span>
                  <p>No registered people yet</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {people.map((p) => (
                    <div className="person-card" key={p.name}>
                      <div className="person-avatar">👤</div>
                      <div className="person-info">
                        <div className="person-name">{p.name}</div>
                        <div className="person-detail">
                          {p.imageCount} images
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <TrainModel />
        </div>
      </div>
    </div>
  );
}
