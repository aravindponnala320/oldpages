"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { adminFetch } from "../../lib/api";

interface ModerationCase {
  id: string;
  assigned_moderator_user_id?: string | null;
  report: {
    reason: string;
    target: {
      id?: string | null;
      type: string;
    };
  };
  severity: string;
  status: string;
  priority_score: number;
  summary: string;
  created_at: string;
}

interface ModerationCasesResponse {
  items: ModerationCase[];
  next_cursor?: string | null;
}

export default function ModerationPage() {
  const router = useRouter();
  const [cases, setCases] = useState<ModerationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState("open");
  const [total, setTotal] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const [cursorStack, setCursorStack] = useState<string[]>([]);
  const [assignLoading, setAssignLoading] = useState<string | null>(null);

  async function fetchCases(useCursor?: string) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", "50");
      if (filterStatus) params.set("status", filterStatus);
      if (useCursor) params.set("cursor", useCursor);
      const data = await adminFetch<ModerationCasesResponse & { next_cursor?: string }>(
        `/admin/moderation/cases?${params}`
      );
      setCases(data.items ?? []);
      setTotal(data.items?.length ?? 0);
      setCursor(data.next_cursor ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load moderation cases");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setCursorStack([]);
    fetchCases();
  }, [filterStatus]);

  async function assignToMe(caseId: string) {
    setAssignLoading(caseId);
    try {
      await adminFetch(`/admin/moderation/cases/${caseId}/actions`, {
        method: "POST",
        body: JSON.stringify({
          action_type: "note",
          reason: "Assigned to me",
          metadata: { source: "moderation_queue_assign" },
        }),
      });
      fetchCases();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to assign");
    } finally {
      setAssignLoading(null);
    }
  }

  function nextPage() {
    if (!cursor) return;
    setCursorStack((prev) => {
      const last = cases[0]?.id ?? "";
      return [...prev, last];
    });
    fetchCases(cursor);
  }

  function prevPage() {
    const stack = [...cursorStack];
    const prev = stack.pop();
    setCursorStack(stack);
    fetchCases(prev);
  }

  const severityColor: Record<string, string> = {
    critical: "admin-badge-red",
    high: "admin-badge-red",
    medium: "admin-badge-yellow",
    low: "admin-badge-blue",
  };

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Moderation Cases</h1>
        <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{total} total</span>
      </div>

      <div className="admin-filter-bar">
        <select className="admin-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_review">In Review</option>
          <option value="actioned">Actioned</option>
          <option value="closed">Closed</option>
          <option value="appealed">Appealed</option>
        </select>
      </div>

      {loading && <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}><span className="spinner" /></div>}

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: ".75rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
          {error}
        </div>
      )}

      {!loading && (
        <div className="admin-panel" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Type</th>
                  <th>Assigned To</th>
                  <th>Status</th>
                  <th>Severity</th>
                  <th>Priority</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cases.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No cases found</td></tr>
                ) : cases.map((c) => (
                  <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => router.push(`/reports/${c.id}`)}>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{c.id.slice(0, 8)}…</td>
                    <td><span className="admin-badge admin-badge-blue">{c.report.target.type}</span></td>
                    <td style={{ fontSize: ".8rem" }}>{c.assigned_moderator_user_id ?? <span style={{ color: "#9ca3af" }}>Unassigned</span>}</td>
                    <td>
                      <span className={`admin-badge ${
                        c.status === "open" ? "admin-badge-yellow" :
                        c.status === "in_review" ? "admin-badge-blue" :
                        c.status === "actioned" ? "admin-badge-green" : "admin-badge-gray"
                      }`}>{c.status}</span>
                    </td>
                    <td>
                      <span className={`admin-badge ${severityColor[c.severity] ?? "admin-badge-gray"}`}>
                        {c.severity}
                      </span>
                    </td>
                    <td>{c.priority_score}</td>
                    <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <button
                        className="admin-btn admin-btn-secondary admin-btn-sm"
                        onClick={() => assignToMe(c.id)}
                        disabled={assignLoading === c.id}
                      >
                        {assignLoading === c.id ? "…" : "Assign to me"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && (cursor || cursorStack.length > 0) && (
        <div style={{ display: "flex", gap: ".5rem", marginTop: "1rem", justifyContent: "flex-end" }}>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={cursorStack.length === 0} onClick={prevPage}>Previous</button>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={!cursor} onClick={nextPage}>Next</button>
        </div>
      )}
    </div>
  );
}
