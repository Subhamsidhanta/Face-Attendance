import { useState, useEffect, useCallback } from "react";
import { STREAM_URL, cameraStatus } from "../services/api";

export default function LiveFeed() {
  const [cam, setCam] = useState({ name: "—", open: false });
  const [imgError, setImgError] = useState(false);
  const [streamKey, setStreamKey] = useState(0);

  // Refresh stream by bumping the cache-buster key
  const refreshStream = useCallback(() => {
    setStreamKey((k) => k + 1);
    setImgError(false);
  }, []);

  useEffect(() => {
    const fetchCam = () =>
      cameraStatus()
        .then((c) => {
          setCam(c);
          setImgError(false);
        })
        .catch(() => setCam((prev) => ({ ...prev, open: false })));
    fetchCam();
    const id = setInterval(fetchCam, 4000);

    // Listen for camera-switch events from CameraSettings
    const onSwitch = () => {
      refreshStream();
      fetchCam();
    };
    window.addEventListener("camera-switched", onSwitch);

    return () => {
      clearInterval(id);
      window.removeEventListener("camera-switched", onSwitch);
    };
  }, [refreshStream]);

  const now = new Date().toLocaleTimeString();

  return (
    <div className="feed-container">
      {cam.open && !imgError ? (
        <>
          <img
            src={`${STREAM_URL}?t=${streamKey}`}
            alt="Live Camera Feed"
            onError={() => setImgError(true)}
          />
          <div className="feed-overlay">
            <span className="feed-badge live">
              <span className="rec-dot"></span>
              LIVE
            </span>
            <span className="feed-badge camera">📷 {cam.name}</span>
          </div>
        </>
      ) : (
        <div className="feed-offline">
          <span className="offline-icon">📷</span>
          <p>Camera offline</p>
          <p className="text-sm text-muted">
            Start the backend to begin streaming
          </p>
        </div>
      )}
    </div>
  );
}
