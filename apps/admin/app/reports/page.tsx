"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { adminFetch } from "../../lib/api";

interface Report {
  id: string;
  case_id: string;
  report_type: string;
  reason: string;
  reporter_id?: string;
  target_id?: string;
  severity: string;
  status: string;
  created_at: string;
}

interface ModerationCase {
  id: string;
  created_at: string;
  report: {
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
}

interface ModerationCasesResponse {
  items: ModerationCase[];
  next_cursor?: string | null;
}

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterStatus, setFilterStatus] = useState("open");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const LIMIT = 50;

  async function fetchReports() {
    setLoading(true);
    setError(null);
    setSelected(new Set());
    try {
      const params = new URLSearchParams();
      params.set("limit", String(LIMIT));
      if (filterStatus) params.set("status", filterStatus);
      const data = await adminFetch<ModerationCasesResponse>(`/admin/moderation/cases?${params}`);
      const mapped = (data.items ?? [])
        .map((item) => ({
          id: item.report.id,
          case_id: item.id,
          report_type: item.report.target.type,
          reason: item.report.reason,
          reporter_id: item.report.reporter.id,
          target_id: item.report.target.id ?? undefined,
          severity: item.severity,
          status: item.status,
          created_at: item.created_at,
        }))
        .filter((item) => !filterType || item.report_type === filterType)
        .filter((item) => !filterSeverity || item.severity === filterSeverity);
      setReports(mapped);
      setTotal(mapped.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchReports(); }, [offset, filterType, filterSeverity, filterStatus]);

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === reports.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(reports.map((r) => r.case_id)));
    }
  }

  async function bulkMarkReviewed() {
    setBulkLoading(true);
    try {
      await Promise.all(
        [...selected].map((id) =>
          adminFetch(`/admin/moderation/cases/${id}/actions`, {
            method: "POST",
            body: JSON.stringify({
              action_type: "note",
              reason: "Marked as reviewing",
              metadata: { source: "reports_bulk_review" },
            }),
          })
        )
      );
      fetchReports();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Bulk action failed");
    } finally {
      setBulkLoading(false);
    }
  }

  async function assignToMe(caseId: string) {
    try {
      await adminFetch(`/admin/moderation/cases/${caseId}/actions`, {
        method: "POST",
        body: JSON.stringify({
          action_type: "note",
          reason: "Assigned to me",
          metadata: { source: "reports_assign" },
        }),
      });
      fetchReports();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to assign");
    }
  }

  const severityColor: Record<string, string> = {
    critical: "admin-badge-red",
    high: "admin-badge-red",
    medium: "admin-badge-yellow",
    low: "admin-badge-blue",
  };

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Reports Queue</h1>
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
          {selected.size > 0 && (
            <button className="admin-btn admin-btn-primary admin-btn-sm" onClick={bulkMarkReviewed} disabled={bulkLoading}>
              {bulkLoading ? "Processing…" : `Mark ${selected.size} Reviewing`}
            </button>
          )}
          <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{total} total</span>
        </div>
      </div>

      <div className="admin-filter-bar">
        <select className="admin-select" value={filterType} onChange={(e) => { setFilterType(e.target.value); setOffset(0); }}>
          <option value="">All types</option>
          <option value="user">User</option>
          <option value="listing">Listing</option>
          <option value="message">Message</option>
          <option value="community">Community</option>
        </select>
        <select className="admin-select" value={filterSeverity} onChange={(e) => { setFilterSeverity(e.target.value); setOffset(0); }}>
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select className="admin-select" value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setOffset(0); }}>
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
                  <th><input type="checkbox" checked={selected.size === reports.length && reports.length > 0} onChange={toggleAll} /></th>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Reason</th>
                  <th>Reporter</th>
                  <th>Target</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.length === 0 ? (
                  <tr><td colSpan={10} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No reports found</td></tr>
                ) : reports.map((report) => (
                  <tr key={report.case_id} style={{ cursor: "pointer" }} onClick={() => router.push(`/reports/${report.case_id}`)}>
                    <td onClick={(e) => e.stopPropagation()}>
                      <input type="checkbox" checked={selected.has(report.case_id)} onChange={() => toggleSelect(report.case_id)} />
                    </td>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{report.id.slice(0, 8)}…</td>
                    <td><span className="admin-badge admin-badge-blue">{report.report_type}</span></td>
                    <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{report.reason}</td>
                    <td style={{ fontSize: ".8rem" }}>{report.reporter_id ?? "—"}</td>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{report.target_id ? report.target_id.slice(0, 8) + "…" : "—"}</td>
                    <td>
                      <span className={`admin-badge ${severityColor[report.severity] ?? "admin-badge-gray"}`}>
                        {report.severity}
                      </span>
                    </td>
                    <td>
                      <span className={`admin-badge ${
                        report.status === "open" ? "admin-badge-yellow" :
                        report.status === "in_review" ? "admin-badge-blue" :
                        report.status === "actioned" ? "admin-badge-green" : "admin-badge-gray"
                      }`}>{report.status}</span>
                    </td>
                    <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(report.created_at).toLocaleDateString()}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => assignToMe(report.case_id)}>Assign to me</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && totalPages > 1 && (
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center", marginTop: "1rem", justifyContent: "flex-end" }}>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>Previous</button>
          <span style={{ fontSize: ".875rem", color: "#5c6670" }}>Page {currentPage} of {totalPages}</span>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={offset + LIMIT >= total} onClick={() => setOffset(offset + LIMIT)}>Next</button>
        </div>
      )}
    </div>
  );
}
