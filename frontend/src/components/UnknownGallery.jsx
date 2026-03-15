import { useState, useEffect } from "react";
import { listUnknown, unknownImageUrl } from "../services/api";

export default function UnknownGallery() {
  const [captures, setCaptures] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    listUnknown().then(setCaptures).catch(() => {});
  }, []);

  const refresh = () => listUnknown().then(setCaptures).catch(() => {});

  // Format timestamp folder name to readable date
  const formatTs = (ts) => {
    // ts like "20260219_123456"
    if (ts.length >= 15) {
      const y = ts.slice(0, 4);
      const mo = ts.slice(4, 6);
      const d = ts.slice(6, 8);
      const h = ts.slice(9, 11);
      const mi = ts.slice(11, 13);
      const s = ts.slice(13, 15);
      return `${y}-${mo}-${d} ${h}:${mi}:${s}`;
    }
    return ts;
  };

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Unknown Person Gallery</h2>
          <p>Captured images of unrecognised faces with camera watermarks</p>
        </div>
        <button className="btn btn-outline" onClick={refresh}>
          ↻ Refresh
        </button>
      </div>

      {captures.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <div className="empty-state">
              <span className="empty-icon">🛡</span>
              <p>No unknown person captures yet</p>
              <p className="text-sm text-muted">
                When an unrecognised face is detected, images will appear here
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-5 stagger-in">
          {captures.map((cap) => (
            <div className="card" key={cap.id}>
              <div className="card-header">
                <h3>
                  ⚠ Capture — {formatTs(cap.timestamp)}
                </h3>
                <span className="tag tag-red">{cap.count} images</span>
              </div>
              <div className="card-body">
                <div className="image-grid">
                  {cap.images.map((img) => (
                    <div
                      className="image-card"
                      key={img}
                      onClick={() =>
                        setSelected(unknownImageUrl(cap.id, img))
                      }
                      style={{ cursor: "pointer" }}
                    >
                      <img
                        src={unknownImageUrl(cap.id, img)}
                        alt={`Unknown - ${img}`}
                        loading="lazy"
                      />
                      <div className="image-meta">{img}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {selected && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: "rgba(0,0,0,0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
          onClick={() => setSelected(null)}
        >
          <img
            src={selected}
            alt="Enlarged unknown capture"
            style={{
              maxWidth: "90vw",
              maxHeight: "90vh",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border)",
            }}
          />
        </div>
      )}
    </div>
  );
}
