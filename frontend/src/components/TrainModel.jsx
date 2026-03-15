import { useState, useEffect, useRef } from "react";
import { trainModel, trainingStatus, reloadModels } from "../services/api";

export default function TrainModel() {
  const [status, setStatus] = useState({ training: false, progress: "" });
  const pollRef = useRef(null);

  const handleTrain = async () => {
    const res = await trainModel();
    if (res.ok) {
      setStatus({ training: true, progress: "Starting..." });
    }
  };

  // Poll while training
  useEffect(() => {
    if (status.training) {
      pollRef.current = setInterval(async () => {
        const s = await trainingStatus();
        setStatus(s);
        if (!s.training) {
          clearInterval(pollRef.current);
          // Auto-reload models after training
          await reloadModels();
        }
      }, 1000);
    }
    return () => clearInterval(pollRef.current);
  }, [status.training]);

  return (
    <div className="card">
      <div className="card-header">
        <h3>🧠 Model Training</h3>
        {status.training && <span className="tag tag-amber">Training…</span>}
      </div>
      <div className="card-body flex flex-col gap-4">
        <p className="text-sm text-muted" style={{ lineHeight: 1.5 }}>
          Train the LBPH face recognition model on all registered faces.
          Run this after adding new people.
        </p>

        {status.progress && (
          <div
            style={{
              padding: "var(--space-3) var(--space-4)",
              background: "var(--bg-base)",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.78rem",
              color: status.progress.includes("✅")
                ? "var(--green)"
                : status.progress.includes("Error")
                ? "var(--red)"
                : "var(--text-secondary)",
            }}
          >
            {status.progress}
          </div>
        )}

        <button
          className="btn btn-primary w-full"
          onClick={handleTrain}
          disabled={status.training}
        >
          {status.training ? "⏳ Training..." : "▶ Train Model"}
        </button>
      </div>
    </div>
  );
}
