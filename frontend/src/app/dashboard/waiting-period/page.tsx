"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Hourglass, Loader2, CheckCircle2, Clock, HelpCircle } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

interface WaitingPeriodEntry {
  condition: string;
  duration_as_stated: string;
  risk_level: string;
  status: "lapsed" | "applies" | "exception_applies" | "may_apply_insufficient_evidence" | "unclear";
  exceptions_found?: string[];
  lapses_on?: string;
  days_remaining?: number;
  note: string;
}

export default function WaitingPeriodPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [asOfDate, setAsOfDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [accident, setAccident] = useState<"unknown" | "yes" | "no">("unknown");
  const [accidentDate, setAccidentDate] = useState("");
  const [claimDocIds, setClaimDocIds] = useState<string[]>([]);
  const [allDocs, setAllDocs] = useState<Document[]>([]);
  const [result, setResult] = useState<{ inception_date: string | null; checked_as_of: string; waiting_periods: WaitingPeriodEntry[]; disclaimer: string } | null>(null);

  useEffect(() => {
    documentsApi.list().then((res) =>
      { setAllDocs(res.data.filter((d: Document) => d.ocr_status === "done"));
        setDocs(res.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done")); }
    ).catch(() => {});
  }, []);

  const runCheck = async () => {
    if (!documentId) {
      toast.error("Pick a policy document first");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.checkWaitingPeriods(documentId, asOfDate || undefined, {
        accident_related: accident === "unknown" ? null : accident === "yes",
        accident_date: accidentDate || undefined,
        claim_document_ids: claimDocIds,
      });
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not check waiting periods");
    } finally {
      setLoading(false);
    }
  };

  const statusStyle = (status: string) =>
    status === "lapsed" ? { color: "#4ADE80", icon: CheckCircle2, label: "LAPSED" }
    : status === "exception_applies" ? { color: "#60A5FA", icon: CheckCircle2, label: "EXCEPTION MAY APPLY" }
    : status === "applies" ? { color: "#FBBF24", icon: Clock, label: "MAY AFFECT CLAIM" }
    : status === "may_apply_insufficient_evidence" ? { color: "#A78BFA", icon: HelpCircle, label: "EVIDENCE INSUFFICIENT" }
    : { color: "#9CA3AF", icon: HelpCircle, label: "UNCLEAR" };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Hourglass size={22} style={{ color: "#A78BFA" }} /> Waiting Period Check
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Check whether a condition's waiting period has lapsed, then whether an exception (such as an accident)
          may apply. Dates are computed directly from your policy's inception date and clauses; no AI guesswork.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div>
          <label className="label">Policy document</label>
          <select className="input" value={documentId} onChange={(e) => setDocumentId(e.target.value)} suppressHydrationWarning>
            <option value="">Select a policy...</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>{d.file_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Check as of (optional)</label>
          <input
            type="date"
            className="input"
            value={asOfDate}
            onChange={(e) => setAsOfDate(e.target.value)}
            suppressHydrationWarning
          />
          <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
            Leave blank to check as of today, or set your treatment date to check whether the period had lapsed then.
          </p>
        </div>

        <div>
          <label className="label">Was the treatment due to an accident? (optional)</label>
          <select className="input" value={accident} onChange={(e) => setAccident(e.target.value as any)} suppressHydrationWarning>
            <option value="unknown">Not sure / not stated</option>
            <option value="yes">Yes, it followed an accident</option>
            <option value="no">No, it was not accident-related</option>
          </select>
          {accident === "yes" && (
            <input type="date" className="input mt-2" value={accidentDate} onChange={(e) => setAccidentDate(e.target.value)} suppressHydrationWarning />
          )}
          <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
            Policies often exempt accident-related treatment from specific waiting periods. This is checked before any status is given.
          </p>
        </div>

        <div>
          <label className="label">Claim documents to scan for accident evidence (optional)</label>
          <select multiple className="input h-24" value={claimDocIds}
            onChange={(e) => setClaimDocIds(Array.from(e.target.selectedOptions).map((o) => o.value))} suppressHydrationWarning>
            {allDocs.filter((d) => d.doc_type !== "policy").map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
          </select>
        </div>

        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Checking...</> : "Check waiting periods"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Policy inception: {result.inception_date || "not found on file"} · Checked as of {result.checked_as_of}
          </p>

          {result.waiting_periods.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              No waiting-period clauses were found on this policy's extraction.
            </p>
          ) : (
            <div className="space-y-3">
              {result.waiting_periods.map((wp, i) => {
                const s = statusStyle(wp.status);
                const Icon = s.icon;
                return (
                  <div key={i} className="rounded-xl p-4" style={{ background: "var(--surface-2)", border: `1px solid ${s.color}30` }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{wp.condition}</p>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Stated duration: {wp.duration_as_stated}</p>
                      </div>
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full shrink-0"
                        style={{ background: `${s.color}1A`, color: s.color }}>
                        <Icon size={12} /> {s.label}
                      </span>
                    </div>
                    <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>{wp.note}</p>
                  </div>
                );
              })}
            </div>
          )}

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
