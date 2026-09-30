"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { claimsApi, appealsApi, analysisApi } from "@/lib/api";
import { ResultActionBar } from "@/components/shared/ResultActionBar";
import toast from "react-hot-toast";
import { format } from "date-fns";
import {
  Loader2, Download, CheckCircle2, XCircle, Clock, FileText,
  ArrowLeft, Users, ChevronDown, AlertTriangle, Scale,
} from "lucide-react";

interface TimelineEvent {
  date: string;
  type: string;
  title: string;
  status: string;
  appeal_id?: string;
}
interface UpcomingDeadline {
  date: string;
  type: string;
  title: string;
  is_overdue: boolean;
  days_remaining: number;
}

const RELATIONSHIP_OPTIONS = ["self", "spouse", "child", "parent", "other"];

const OUTCOME_STYLES: Record<string, { color: string; icon: any; label: string }> = {
  pending: { color: "#FBBF24", icon: Clock, label: "Pending" },
  approved: { color: "#4ADE80", icon: CheckCircle2, label: "Approved" },
  rejected: { color: "#F87171", icon: XCircle, label: "Rejected" },
  partial: { color: "#60A5FA", icon: CheckCircle2, label: "Partially Approved" },
};

export default function ClaimDetailPage() {
  const params = useParams();
  const claimId = params.id as string;

  const [claim, setClaim] = useState<any>(null);
  const [timeline, setTimeline] = useState<{ events: TimelineEvent[]; upcoming_deadlines: UpcomingDeadline[] } | null>(null);
  const [appeals, setAppeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [editingPatient, setEditingPatient] = useState(false);
  const [patientName, setPatientName] = useState("");
  const [patientRelationship, setPatientRelationship] = useState("self");
  const [savingPatient, setSavingPatient] = useState(false);
  const [outcomeSaving, setOutcomeSaving] = useState<string | null>(null);
  const [costBenefit, setCostBenefit] = useState<any>(null);
  const [loadingCostBenefit, setLoadingCostBenefit] = useState(false);
  const [followupLetter, setFollowupLetter] = useState<any>(null);
  const [loadingFollowup, setLoadingFollowup] = useState<string | null>(null);
  const [precedents, setPrecedents] = useState<any>(null);
  const [loadingPrecedents, setLoadingPrecedents] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [claimRes, timelineRes, appealsRes] = await Promise.all([
        claimsApi.get(claimId),
        claimsApi.getTimeline(claimId),
        appealsApi.listForClaim(claimId),
      ]);
      setClaim(claimRes.data);
      setTimeline(timelineRes.data);
      setAppeals(appealsRes.data || []);
      setPatientName(claimRes.data.patient_name || "");
      setPatientRelationship(claimRes.data.patient_relationship || "self");
    } catch {
      toast.error("Couldn't load this claim.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (claimId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  const handleSavePatient = async () => {
    setSavingPatient(true);
    try {
      await claimsApi.updatePatient(claimId, {
        patient_name: patientRelationship === "self" ? null : patientName.trim() || null,
        patient_relationship: patientRelationship,
      });
      toast.success("Updated who this claim is for.");
      setEditingPatient(false);
      load();
    } catch {
      toast.error("Couldn't save. Please try again.");
    } finally {
      setSavingPatient(false);
    }
  };

  const handleExportPdf = async () => {
    setExporting(true);
    try {
      const res = await claimsApi.exportPdf(claimId);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `redoclaim-audit-trail-${claim?.policy_number || claimId.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Couldn't generate the PDF. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const runCostBenefit = async () => {
    setLoadingCostBenefit(true);
    try {
      const res = await analysisApi.costBenefit(claimId);
      setCostBenefit(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Couldn't run the cost-benefit check.");
    } finally {
      setLoadingCostBenefit(false);
    }
  };

  const runFollowup = async (deadlineType: "gro" | "irdai") => {
    setLoadingFollowup(deadlineType);
    try {
      const res = await analysisApi.generateFollowup(claimId, deadlineType);
      setFollowupLetter(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Couldn't generate a follow-up letter.");
    } finally {
      setLoadingFollowup(null);
    }
  };

  const runPrecedentMatch = async () => {
    setLoadingPrecedents(true);
    try {
      const res = await analysisApi.matchPrecedents({ claim_id: claimId });
      setPrecedents(res.data);
    } catch {
      toast.error("Couldn't find precedents.");
    } finally {
      setLoadingPrecedents(false);
    }
  };

  const handleOutcomeChange = async (appealId: string, outcome: string) => {
    setOutcomeSaving(appealId);
    try {
      await appealsApi.updateOutcome(appealId, outcome as any);
      toast.success("Outcome updated.");
      load();
    } catch {
      toast.error("Couldn't update outcome.");
    } finally {
      setOutcomeSaving(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="animate-spin" size={28} style={{ color: "var(--text-tertiary)" }} />
      </div>
    );
  }

  if (!claim) {
    return <p style={{ color: "var(--text-secondary)" }}>Claim not found.</p>;
  }

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <Link href="/dashboard/timeline" className="inline-flex items-center gap-1.5 text-sm font-medium transition"
        style={{ color: "var(--text-tertiary)" }}>
        <ArrowLeft size={14} /> Back to all claims
      </Link>

      {/* Header / summary */}
      <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{claim.insurer_name}</h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              Policy {claim.policy_number || "—"} · {claim.insurance_type?.toUpperCase()}
              {claim.claim_amount ? ` · ₹${claim.claim_amount.toLocaleString("en-IN")}` : ""}
            </p>
          </div>
          <button
            onClick={handleExportPdf}
            disabled={exporting}
            className="btn-secondary inline-flex items-center gap-2 py-2 px-4"
            suppressHydrationWarning>
            {exporting ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
            Export audit trail (PDF)
          </button>
        </div>

        {/* Family / patient assignment */}
        <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--surface-5)" }}>
          {!editingPatient ? (
            <button
              onClick={() => setEditingPatient(true)}
              className="inline-flex items-center gap-2 text-sm font-medium transition"
              style={{ color: "#A78BFA" }}
              suppressHydrationWarning>
              <Users size={14} />
              {claim.patient_name
                ? `Filed for: ${claim.patient_name} (${claim.patient_relationship || "family member"})`
                : "Filed for: yourself — click to reassign"}
            </button>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={patientRelationship}
                onChange={(e) => setPatientRelationship(e.target.value)}
                className="input py-1.5 text-sm w-auto"
                suppressHydrationWarning>
                {RELATIONSHIP_OPTIONS.map((r) => (
                  <option key={r} value={r}>{r === "self" ? "Myself" : r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
              {patientRelationship !== "self" && (
                <input
                  className="input py-1.5 text-sm w-auto"
                  placeholder="Name"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  suppressHydrationWarning
                />
              )}
              <button onClick={handleSavePatient} disabled={savingPatient} className="btn-primary py-1.5 px-3 text-sm" suppressHydrationWarning>
                {savingPatient ? <Loader2 size={13} className="animate-spin" /> : "Save"}
              </button>
              <button onClick={() => setEditingPatient(false)} className="text-sm" style={{ color: "var(--text-tertiary)" }} suppressHydrationWarning>
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Upcoming deadlines */}
      {timeline && timeline.upcoming_deadlines.length > 0 && (
        <div className="space-y-2">
          {timeline.upcoming_deadlines.map((d, i) => (
            <div key={i} className="rounded-xl p-4 flex items-center gap-3"
              style={{
                background: d.is_overdue ? "rgba(248,113,113,0.08)" : "rgba(251,191,36,0.08)",
                border: `1px solid ${d.is_overdue ? "rgba(248,113,113,0.2)" : "rgba(251,191,36,0.2)"}`,
              }}>
              <AlertTriangle size={16} style={{ color: d.is_overdue ? "#F87171" : "#FBBF24" }} />
              <p className="text-sm flex-1" style={{ color: "var(--text-primary)" }}>
                <strong>{d.title}</strong> — {d.is_overdue
                  ? `overdue since ${format(new Date(d.date), "d MMM yyyy")}`
                  : `${d.days_remaining} day(s) left, due ${format(new Date(d.date), "d MMM yyyy")}`}
              </p>
              {d.is_overdue && (
                <button
                  onClick={() => runFollowup(d.type === "gro_deadline" ? "gro" : "irdai")}
                  disabled={loadingFollowup !== null}
                  className="btn-secondary text-xs px-2.5 py-1.5 shrink-0"
                  suppressHydrationWarning>
                  {loadingFollowup === (d.type === "gro_deadline" ? "gro" : "irdai") ? <Loader2 size={12} className="animate-spin" /> : "Draft follow-up"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {followupLetter && (
        <div id="followup-letter-result" className="card p-6 space-y-3" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{followupLetter.subject}</h3>
          <pre className="whitespace-pre-wrap text-xs font-mono p-3 rounded-lg" style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}>
            {followupLetter.letter_content}
          </pre>
          <ResultActionBar emailBody={followupLetter.letter_content} subject={followupLetter.subject} printTargetId="followup-letter-result" />
          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>{followupLetter.disclaimer}</p>
        </div>
      )}

      {/* Cost-benefit advisor */}
      {claim.audit_report && claim.status !== "resolved" && (
        <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold flex items-center gap-1.5" style={{ color: "var(--text-primary)" }}>
              <Scale size={15} /> Is it worth pursuing?
            </h2>
            {!costBenefit && (
              <button onClick={runCostBenefit} disabled={loadingCostBenefit} className="btn-secondary text-xs px-3 py-1.5" suppressHydrationWarning>
                {loadingCostBenefit ? <Loader2 size={12} className="animate-spin" /> : "Check"}
              </button>
            )}
          </div>
          {costBenefit && (
            <div className="space-y-3">
              <p className="text-sm font-medium" style={{
                color: costBenefit.verdict === "strongly_worth_fighting" ? "#4ADE80"
                  : costBenefit.verdict === "not_worth_fighting" ? "#F87171" : "#FBBF24",
              }}>
                {costBenefit.headline}
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-lg p-3" style={{ background: "var(--surface-2)" }}>
                  <p style={{ color: "var(--text-tertiary)" }}>Recommended route</p>
                  <p className="font-medium mt-0.5" style={{ color: "var(--text-primary)" }}>{costBenefit.recommended_route_label}</p>
                </div>
                <div className="rounded-lg p-3" style={{ background: "var(--surface-2)" }}>
                  <p style={{ color: "var(--text-tertiary)" }}>Estimated effort</p>
                  <p className="font-medium mt-0.5" style={{ color: "var(--text-primary)" }}>~{costBenefit.estimated_effort_hours}h (₹{costBenefit.estimated_effort_value.toLocaleString("en-IN")} of your time)</p>
                </div>
              </div>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{costBenefit.reasoning}</p>
              <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>{costBenefit.disclaimer}</p>
            </div>
          )}
        </div>
      )}

      {/* Legal precedent matcher */}
      {claim.audit_report && (
        <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold flex items-center gap-1.5" style={{ color: "var(--text-primary)" }}>
              <Scale size={15} /> Similar cases others have won
            </h2>
            {!precedents && (
              <button onClick={runPrecedentMatch} disabled={loadingPrecedents} className="btn-secondary text-xs px-3 py-1.5" suppressHydrationWarning>
                {loadingPrecedents ? <Loader2 size={12} className="animate-spin" /> : "Find precedents"}
              </button>
            )}
          </div>
          {precedents && (
            <div className="space-y-3">
              {precedents.precedents.length === 0 ? (
                <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>No closely matching precedents found in our library for this case type.</p>
              ) : (
                precedents.precedents.map((p: any) => (
                  <div key={p.id} className="rounded-lg p-3" style={{ background: "var(--surface-2)" }}>
                    <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{p.case_name}</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>{p.court}</p>
                    <p className="text-xs mt-1.5" style={{ color: "var(--text-secondary)" }}>{p.summary}</p>
                    <p className="text-xs mt-1.5 font-medium" style={{ color: "#A78BFA" }}>How to use: {p.how_to_use}</p>
                  </div>
                ))
              )}
              <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>{precedents.disclaimer}</p>
            </div>
          )}
        </div>
      )}

      {/* Status timeline */}
      <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Case timeline</h2>
        {timeline && timeline.events.length > 0 ? (
          <ol className="relative border-l pl-5 space-y-6" style={{ borderColor: "var(--surface-5)" }}>
            {timeline.events.map((ev, i) => (
              <li key={i} className="relative">
                <span
                  className="absolute -left-[27px] top-1 w-3 h-3 rounded-full"
                  style={{
                    background: ev.status === "done" || ev.status === "approved" ? "#4ADE80"
                      : ev.status === "rejected" ? "#F87171"
                      : ev.status === "drafted" || ev.status === "partial" ? "#FBBF24"
                      : "#8B5CF6",
                  }}
                />
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{ev.title}</p>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                  {format(new Date(ev.date), "d MMM yyyy")}
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>No events recorded yet.</p>
        )}
      </div>

      {/* Appeals + outcome tracking */}
      {appeals.length > 0 && (
        <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Appeals filed</h2>
          <div className="space-y-3">
            {appeals.map((a) => {
              const outcome = OUTCOME_STYLES[a.outcome || "pending"];
              const Icon = outcome.icon;
              return (
                <div key={a.id} className="flex items-center justify-between gap-3 rounded-lg p-3"
                  style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                  <div className="flex items-center gap-2.5">
                    <FileText size={15} style={{ color: "var(--text-tertiary)" }} />
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {String(a.appeal_type).replace("_", " ").toUpperCase()}
                    </span>
                  </div>
                  <div className="relative">
                    <select
                      value={a.outcome || "pending"}
                      onChange={(e) => handleOutcomeChange(a.id, e.target.value)}
                      disabled={outcomeSaving === a.id}
                      className="appearance-none pl-7 pr-7 py-1.5 rounded-lg text-xs font-semibold cursor-pointer"
                      style={{ background: `${outcome.color}1A`, color: outcome.color, border: `1px solid ${outcome.color}40` }}
                      suppressHydrationWarning>
                      {Object.entries(OUTCOME_STYLES).map(([key, val]) => (
                        <option key={key} value={key}>{val.label}</option>
                      ))}
                    </select>
                    <Icon size={12} className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: outcome.color }} />
                    <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: outcome.color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
