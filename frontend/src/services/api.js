const API_BASE = "http://localhost:8000";

// ── Camera ────────────────────────────────────────────────────────────
export const STREAM_URL = `${API_BASE}/api/camera/stream`;

export async function listCameras() {
  const res = await fetch(`${API_BASE}/api/camera/list`);
  return res.json();
}

export async function changeCamera(index) {
  const res = await fetch(`${API_BASE}/api/camera/change`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index }),
  });
  return res.json();
}

export async function cameraStatus() {
  const res = await fetch(`${API_BASE}/api/camera/status`);
  return res.json();
}

// ── Attendance ────────────────────────────────────────────────────────
export async function getAttendance(date) {
  const url = date
    ? `${API_BASE}/api/attendance?date=${date}`
    : `${API_BASE}/api/attendance`;
  const res = await fetch(url);
  return res.json();
}

export async function startMonitoring() {
  const res = await fetch(`${API_BASE}/api/attendance/start`, { method: "POST" });
  return res.json();
}

export async function stopMonitoring() {
  const res = await fetch(`${API_BASE}/api/attendance/stop`, { method: "POST" });
  return res.json();
}

export async function monitoringStatus() {
  const res = await fetch(`${API_BASE}/api/attendance/status`);
  return res.json();
}

// ── Registration ──────────────────────────────────────────────────────
export async function startRegistration(name, captureLimit = 250) {
  const res = await fetch(`${API_BASE}/api/register/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, captureLimit }),
  });
  return res.json();
}

export async function stopRegistration() {
  const res = await fetch(`${API_BASE}/api/register/stop`, { method: "POST" });
  return res.json();
}

export async function registrationStatus() {
  const res = await fetch(`${API_BASE}/api/register/status`);
  return res.json();
}

export async function listRegistered() {
  const res = await fetch(`${API_BASE}/api/register/list`);
  return res.json();
}

// ── Training ──────────────────────────────────────────────────────────
export async function trainModel() {
  const res = await fetch(`${API_BASE}/api/train`, { method: "POST" });
  return res.json();
}

export async function trainingStatus() {
  const res = await fetch(`${API_BASE}/api/train/status`);
  return res.json();
}

export async function reloadModels() {
  const res = await fetch(`${API_BASE}/api/train/reload`, { method: "POST" });
  return res.json();
}

// ── Alerts ────────────────────────────────────────────────────────────
export function connectAlerts(onEvent) {
  const es = new EventSource(`${API_BASE}/api/alerts`);
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch { /* heartbeat */ }
  };
  es.onerror = () => {
    console.warn("[SSE] Connection error, will retry...");
  };
  return es;
}

export async function stopAlert() {
  const res = await fetch(`${API_BASE}/api/alerts/stop`, { method: "POST" });
  return res.json();
}

export async function isAlertActive() {
  const res = await fetch(`${API_BASE}/api/alerts/active`);
  return res.json();
}

// ── Unknown captures ──────────────────────────────────────────────────
export async function listUnknown() {
  const res = await fetch(`${API_BASE}/api/unknown`);
  return res.json();
}

export function unknownImageUrl(folder, filename) {
  return `${API_BASE}/api/unknown/${folder}/${filename}`;
}

// ── Health ────────────────────────────────────────────────────────────
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
