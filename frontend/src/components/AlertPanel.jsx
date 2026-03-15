import { useState, useEffect, useRef } from "react";
import { connectAlerts, stopAlert, isAlertActive } from "../services/api";

export default function AlertPanel() {
  const [alert, setAlert] = useState(null);
  const [active, setActive] = useState(false);
  const alarmIntervalRef = useRef(null);
  const audioCtxRef = useRef(null);

  const beep = () => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") {
        ctx.resume();
      }

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      gain.gain.value = 0.22;
      osc.start();
      osc.stop(ctx.currentTime + 0.22);
    } catch {}
  };

  const startAlarmLoop = () => {
    if (alarmIntervalRef.current) return;
    beep();
    alarmIntervalRef.current = setInterval(beep, 800);
  };

  const stopAlarmLoop = () => {
    if (alarmIntervalRef.current) {
      clearInterval(alarmIntervalRef.current);
      alarmIntervalRef.current = null;
    }
  };

  // On mount — check if an alert is already active (handles page refresh)
  useEffect(() => {
    isAlertActive()
      .then((data) => {
        if (data.active) {
          setActive(true);
          startAlarmLoop();
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const es = connectAlerts((event) => {
      if (event.type === "alert_start") {
        setAlert(event);
        setActive(true);
        startAlarmLoop();
      } else if (event.type === "alert_persist") {
        // Unknown person is still there — keep alarm going
        if (!alarmIntervalRef.current) {
          setActive(true);
          startAlarmLoop();
        }
      } else if (event.type === "capture_complete") {
        // Images captured — but do NOT stop alarm.
        // Alarm only stops on manual STOP button click.
      } else if (event.type === "alert_stop") {
        setActive(false);
        stopAlarmLoop();
      }
    });
    return () => {
      es.close();
      stopAlarmLoop();
      if (audioCtxRef.current) {
        try {
          audioCtxRef.current.close();
        } catch {}
        audioCtxRef.current = null;
      }
    };
  }, []);

  const handleStop = async () => {
    await stopAlert();
    setActive(false);
    stopAlarmLoop();
  };

  return (
    <div className={`alert-panel ${active ? "alert-active" : "alert-idle"}`}>
      {active ? (
        <>
          <span className="alert-icon">🚨</span>
          <div className="alert-content">
            <h4>UNKNOWN PERSON</h4>
            <p>
              {alert?.camera || "—"} · Alert active
            </p>
          </div>
          <button className="btn btn-danger btn-sm" onClick={handleStop}>
            ■ STOP
          </button>
        </>
      ) : (
        <>
          <span className="alert-icon-sm">🛡</span>
          <span className="alert-idle-text">All Clear</span>
        </>
      )}
    </div>
  );
}
