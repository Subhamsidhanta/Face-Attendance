import CameraSettings from "../components/CameraSettings";
import LiveFeed from "../components/LiveFeed";

export default function Settings() {
  return (
    <div>
      <div className="page-header">
        <h2>Settings</h2>
        <p>Camera configuration and system preferences</p>
      </div>

      <div className="grid-2">
        <div className="flex flex-col gap-5">
          <CameraSettings />

          <div className="card">
            <div className="card-header">
              <h3>ℹ System Info</h3>
            </div>
            <div className="card-body flex flex-col gap-3">
              <div className="flex justify-between">
                <span className="text-sm text-muted">Backend</span>
                <span className="text-sm">FastAPI (Python)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted">Recognition</span>
                <span className="text-sm">LBPH (OpenCV)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted">Liveness</span>
                <span className="text-sm">CNN (PyTorch)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted">Blink Detection</span>
                <span className="text-sm">MediaPipe EAR</span>
              </div>
            </div>
          </div>
        </div>

        <div>
          <LiveFeed />
          <p className="text-sm text-muted mt-3">
            Camera preview — switch cameras using the dropdown to the left
          </p>
        </div>
      </div>
    </div>
  );
}
