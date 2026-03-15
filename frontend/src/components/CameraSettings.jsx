import { useState, useEffect } from "react";
import { listCameras, changeCamera, cameraStatus } from "../services/api";

export default function CameraSettings() {
  const [cameras, setCameras] = useState([]);
  const [current, setCurrent] = useState(null);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    listCameras().then(setCameras).catch(() => {});
    cameraStatus().then(setCurrent).catch(() => {});
  }, []);

  const handleSwitch = async (index) => {
    setSwitching(true);
    try {
      const res = await changeCamera(index);
      if (res.ok) {
        setCurrent({ open: true, index, name: res.camera });
        // Notify all LiveFeed instances to refresh their MJPEG stream
        window.dispatchEvent(new CustomEvent("camera-switched"));
      }
    } catch (e) {
      console.error("Failed to switch camera:", e);
    }
    setSwitching(false);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>📷 Camera</h3>
        {current?.open && (
          <span className="tag tag-green">● {current.name}</span>
        )}
      </div>
      <div className="card-body flex flex-col gap-4">
        <div className="form-group">
          <label className="form-label">Select Camera</label>
          <select
            className="form-select"
            value={current?.index ?? 0}
            onChange={(e) => handleSwitch(Number(e.target.value))}
            disabled={switching}
          >
            {cameras.map((c) => (
              <option key={c.index} value={c.index}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <p className="text-sm text-muted">
          {switching
            ? "Switching camera..."
            : `Currently using ${current?.name || "unknown"}`}
        </p>
      </div>
    </div>
  );
}
