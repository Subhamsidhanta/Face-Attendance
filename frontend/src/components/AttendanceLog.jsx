import { useState, useEffect } from "react";
import { getAttendance } from "../services/api";

export default function AttendanceLog() {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    const fetch = () =>
      getAttendance()
        .then(setRecords)
        .catch(() => {});
    fetch();
    const id = setInterval(fetch, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <h3>📋 Attendance Log</h3>
        <span className="tag tag-green">{records.length} today</span>
      </div>
      <div className="card-body" style={{ maxHeight: 320, overflowY: "auto" }}>
        {records.length === 0 ? (
          <div className="empty-state" style={{ padding: "32px 16px" }}>
            <span className="empty-icon">📝</span>
            <p>No attendance recorded yet today</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={i} className="animate-in" style={{ animationDelay: `${i * 40}ms` }}>
                  <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                    {r.name}
                  </td>
                  <td>{r.date}</td>
                  <td>{r.time}</td>
                  <td>
                    <span className="tag tag-green">✓ Present</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
