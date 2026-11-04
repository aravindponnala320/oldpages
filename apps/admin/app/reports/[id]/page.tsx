"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { adminFetch } from "../../../lib/api";

interface ReportDetail {
  id: string;
  report_type: string;
  reason: string;
  description?: string;
  evidence?: string[];
  severity: string;
  status: string;
  created_at: string;
  reporter?: {
    id: string;
    name?: string;
    email?: string;
  };
  target?: {
    id: string;
    type: string;
    title?: string;
    content?: string;
    user_email?: string;
  };
}

interface ModerationCaseResponse {
  actions: {
    action_type: string;
    actor_user_id?: string | null;
    created_at: string;
    id: string;
    reason?: string | null;
  }[];
  created_at: string;
  id: string;
  report: {
    description?: string | null;
    evidence: Record<string, unknown>;
    id: string;
    reason: string;
    reporter: { id: string };
    target: {
      id?: string | null;
      type: string;
    };
  };
  severity: string;
  status: string;
  summary: string;
}

interface AuditEntry {
  id: string;
  action: string;
  actor_email?: string;
  created_at: string;
  details?: string;
}

interface RelatedReport {
  id: string;
  reason: string;
  severity: string;
  status: string;
  created_at: string;
}

function mapCaseToReport(caseData: ModerationCaseResponse): ReportDetail {
  return {
    id: caseData.id,
    report_type: caseData.report.target.type,
    reason: caseData.report.reason,
    description: caseData.report.description ?? caseData.summary,
    evidence: evidenceLinks(caseData.report.evidence),
    severity: caseData.severity,
    status: caseData.status,
    created_at: caseData.created_at,
    reporter: {
      id: caseData.report.reporter.id,
    },
    target: {
      id: caseData.report.target.id ?? "—",
      type: caseData.report.target.type,
    },
  };
}

function evidenceLinks(evidence: Record<string, unknown>): string[] {
  return Object.values(evidence).flatMap((value) => {
    if (typeof value === "string" && value.startsWith("http")) return [value];
    if (Array.isArray(value)) {
      return value.filter((item): item is string => typeof item === "string" && item.startsWith("http"));
    }
    return [];
  });
}

function durationToIso(duration: string): string | undefined {
  if (duration === "permanent") return undefined;
  const days = Number.parseInt(duration, 10);
  if (!Number.isFinite(days)) return undefined;
  const until = new Date();
  until.setDate(until.getDate() + days);
  return until.toISOString();
}

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [related, setRelated] = useState<RelatedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Moderation action form
  const [actionType, setActionType] = useState("warn");
  const [duration, setDuration] = useState("7d");
  const [actionReason, setActionReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const caseData = await adminFetch<ModerationCaseResponse>(`/admin/moderation/cases/${reportId}`);
        setReport(mapCaseToReport(caseData));
        setAudit(caseData.actions.map((entry) => ({
          id: entry.id,
          action: entry.action_type,
          actor_email: entry.actor_user_id ?? undefined,
          created_at: entry.created_at,
          details: entry.reason ?? undefined,
        })));
        setRelated([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [reportId]);

  async function handleTakeAction(e: React.FormEvent) {
    e.preventDefault();
    setActionLoading(true);
    setActionSuccess(false);
    try {
      const body: Record<string, unknown> = {
        action_type: actionType,
        reason: actionReason,
        metadata: { source: "report_detail" },
      };
      const durationUntil = durationToIso(duration);
      if (durationUntil) {
        body.duration_until = durationUntil;
      }
      await adminFetch(`/admin/moderation/cases/${reportId}/actions`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setActionSuccess(true);
      setActionReason("");
      const updated = await adminFetch<ModerationCaseResponse>(`/admin/moderation/cases/${reportId}`);
      setReport(mapCaseToReport(updated));
      setAudit(updated.actions.map((entry) => ({
        id: entry.id,
        action: entry.action_type,
        actor_email: entry.actor_user_id ?? undefined,
        created_at: entry.created_at,
        details: entry.reason ?? undefined,
      })));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  }

  const severityColor: Record<string, string> = {
    critical: "admin-badge-red",
    high: "admin-badge-red",
    medium: "admin-badge-yellow",
    low: "admin-badge-blue",
  };

  const hasDuration = actionType === "suspend";

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><span className="spinner" /></div>;
  if (error) return <div style={{ color: "#991b1b", padding: "1rem" }}>{error}</div>;
  if (!report) return null;

  return (
    <div>
      <div className="admin-page-header">
        <div style={{ display: "flex", alignItems: "center", gap: ".75rem" }}>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => router.back()}>← Back</button>
          <h1 className="admin-page-title">Report #{report.id.slice(0, 8)}</h1>
        </div>
        <div style={{ display: "flex", gap: ".5rem" }}>
          <span className={`admin-badge ${severityColor[report.severity] ?? "admin-badge-gray"}`}>{report.severity}</span>
          <span className={`admin-badge ${
            report.status === "open" ? "admin-badge-yellow" :
            report.status === "in_review" ? "admin-badge-blue" :
            report.status === "actioned" ? "admin-badge-green" : "admin-badge-gray"
          }`}>{report.status}</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "1.5rem", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Report Summary */}
          <div className="admin-panel">
            <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>Report Summary</h2>
            <dl style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: ".5rem .75rem", margin: 0 }}>
              <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Type</dt>
              <dd style={{ margin: 0 }}><span className="admin-badge admin-badge-blue">{report.report_type}</span></dd>
              <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Reason</dt>
              <dd style={{ margin: 0, fontWeight: 500 }}>{report.reason}</dd>
              {report.description && (
                <>
                  <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Description</dt>
                  <dd style={{ margin: 0, fontSize: ".875rem", color: "#374151" }}>{report.description}</dd>
                </>
              )}
              <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Created</dt>
              <dd style={{ margin: 0, fontSize: ".875rem" }}>{new Date(report.created_at).toLocaleString()}</dd>
            </dl>
            {report.evidence && report.evidence.length > 0 && (
              <div style={{ marginTop: "1rem" }}>
                <div style={{ fontSize: ".8rem", color: "#5c6670", marginBottom: ".5rem" }}>Evidence</div>
                <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
                  {report.evidence.map((url, i) => (
                    <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="admin-btn admin-btn-secondary admin-btn-sm">
                      Evidence {i + 1}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Reporter Info */}
          {report.reporter && (
            <div className="admin-panel">
              <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>Reporter</h2>
              <dl style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: ".5rem .75rem", margin: 0 }}>
                <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Name</dt>
                <dd style={{ margin: 0 }}>{report.reporter.name ?? "—"}</dd>
                <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Email</dt>
                <dd style={{ margin: 0 }}>{report.reporter.email ?? "—"}</dd>
                <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>ID</dt>
                <dd style={{ margin: 0, fontFamily: "monospace", fontSize: ".8rem" }}>{report.reporter.id}</dd>
              </dl>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" style={{ marginTop: ".75rem" }} onClick={() => router.push(`/users/${report.reporter!.id}`)}>
                View User
              </button>
            </div>
          )}

          {/* Target Content */}
          {report.target && (
            <div className="admin-panel">
              <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>
                Target ({report.target.type})
              </h2>
              <dl style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: ".5rem .75rem", margin: 0 }}>
                <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>ID</dt>
                <dd style={{ margin: 0, fontFamily: "monospace", fontSize: ".8rem" }}>{report.target.id}</dd>
                {report.target.title && (
                  <>
                    <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Title</dt>
                    <dd style={{ margin: 0, fontWeight: 500 }}>{report.target.title}</dd>
                  </>
                )}
                {report.target.user_email && (
                  <>
                    <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>User</dt>
                    <dd style={{ margin: 0 }}>{report.target.user_email}</dd>
                  </>
                )}
                {report.target.content && (
                  <>
                    <dt style={{ fontSize: ".8rem", color: "#5c6670" }}>Content</dt>
                    <dd style={{ margin: 0, fontSize: ".875rem", color: "#374151", fontStyle: "italic" }}>&ldquo;{report.target.content}&rdquo;</dd>
                  </>
                )}
              </dl>
            </div>
          )}

          {/* Related Reports */}
          {related.length > 0 && (
            <div className="admin-panel">
              <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>Related Reports</h2>
              <table className="admin-table">
                <thead>
                  <tr><th>ID</th><th>Reason</th><th>Severity</th><th>Status</th><th>Created</th></tr>
                </thead>
                <tbody>
                  {related.map((r) => (
                    <tr key={r.id} style={{ cursor: "pointer" }} onClick={() => router.push(`/reports/${r.id}`)}>
                      <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{r.id.slice(0, 8)}…</td>
                      <td>{r.reason}</td>
                      <td><span className={`admin-badge ${severityColor[r.severity] ?? "admin-badge-gray"}`}>{r.severity}</span></td>
                      <td><span className="admin-badge admin-badge-gray">{r.status}</span></td>
                      <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(r.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Audit History */}
          <div className="admin-panel">
            <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>Audit History</h2>
            {audit.length === 0 ? (
              <p style={{ fontSize: ".875rem", color: "#5c6670" }}>No audit entries yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: ".5rem" }}>
                {audit.map((entry) => (
                  <div key={entry.id} style={{ fontSize: ".8rem", borderLeft: "2px solid #d9ddd6", paddingLeft: ".75rem" }}>
                    <div style={{ fontWeight: 500 }}>{entry.action}</div>
                    {entry.actor_email && <div style={{ color: "#5c6670" }}>by {entry.actor_email}</div>}
                    {entry.details && <div style={{ color: "#374151" }}>{entry.details}</div>}
                    <div style={{ color: "#9ca3af", marginTop: ".2rem" }}>{new Date(entry.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Moderation Action Panel */}
        <div className="admin-panel" style={{ position: "sticky", top: "1rem" }}>
          <h2 style={{ fontSize: ".9rem", fontWeight: 600, margin: "0 0 1rem", color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em" }}>Take Action</h2>

          {actionSuccess && (
            <div style={{ background: "#d1fae5", color: "#065f46", padding: ".75rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
              Action taken successfully.
            </div>
          )}

          <form onSubmit={handleTakeAction} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Action Type</label>
              <select className="admin-select" style={{ width: "100%" }} value={actionType} onChange={(e) => setActionType(e.target.value)}>
                <option value="warn">Warn user</option>
                <option value="remove_content">Remove content</option>
                <option value="suspend">Suspend user</option>
                <option value="ban">Ban user</option>
                <option value="dismiss">Dismiss report</option>
                <option value="restore">Restore</option>
                <option value="note">Add note</option>
              </select>
            </div>

            {hasDuration && (
              <div>
                <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Duration</label>
                <select className="admin-select" style={{ width: "100%" }} value={duration} onChange={(e) => setDuration(e.target.value)}>
                  <option value="1d">1 day</option>
                  <option value="7d">7 days</option>
                  <option value="30d">30 days</option>
                  <option value="permanent">Permanent</option>
                </select>
              </div>
            )}

            <div>
              <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Reason</label>
              <textarea
                className="admin-input"
                rows={4}
                style={{ width: "100%", resize: "vertical" }}
                placeholder="Explain the action taken..."
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className={`admin-btn ${actionType === "dismiss" ? "admin-btn-secondary" : actionType.includes("ban") ? "admin-btn-danger" : "admin-btn-primary"}`}
              style={{ width: "100%", justifyContent: "center" }}
              disabled={actionLoading}
            >
              {actionLoading ? "Processing…" : "Take Action"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
