"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { ShieldAlert, Loader2, CheckCircle2, XCircle, Info } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

export default function PreauthCheckPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [denialDocId, setDenialDocId] = useState("");
  const [policyDocId, setPolicyDocId] = useState("");
  const [treatmentAmount, setTreatmentAmount] = useState("");
  const [reqTime, setReqTime] = useState("");
  const [decTime, setDecTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    documentsApi.list().then((res) => setDocs(res.data.filter((d: Document) => d.ocr_status === "done"))).catch(() => {});
  }, []);

  const policyDocs = docs.filter((d) => d.doc_type === "policy");

  const runCheck = async () => {
    if (!denialDocId) {
      toast.error("Select the pre-auth denial document.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.preauthCheck({
        denial_document_id: denialDocId,
        policy_document_id: policyDocId || undefined,
        treatment_amount: treatmentAmount ? parseFloat(treatmentAmount) : undefined,
        preauth_request_time: reqTime || undefined,
        preauth_decision_time: decTime || undefined,
      });
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not check this denial.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <ShieldAlert size={22} style={{ color: "#A78BFA" }} /> Pre-Authorization Denial Checker
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Your cashless request was denied at admission — before you decide what to do next, check
          whether the denial reason holds up and whether the insurer met the cashless-response timeline.
        </p>
      </div>

      <div className="rounded-xl p-4 flex items-start gap-2.5" style={{ background: "rgba(96,165,250,0.08)", border: "1px solid rgba(96,165,250,0.2)" }}>
        <Info size={15} className="mt-0.5 shrink-0" style={{ color: "#60A5FA" }} />
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          A pre-auth denial is <strong>not</strong> a final rejection — you can still pay out of pocket and
          claim reimbursement under the same policy, regardless of what this check finds.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div>
          <label className="label">Pre-auth denial / query letter</label>
          <select className="input" value={denialDocId} onChange={(e) => setDenialDocId(e.target.value)} suppressHydrationWarning>
            <option value="">Select...</option>
            {docs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
          </select>
        </div>

        <div>
          <label className="label">Policy document (optional, improves accuracy)</label>
          <select className="input" value={policyDocId} onChange={(e) => setPolicyDocId(e.target.value)} suppressHydrationWarning>
            <option value="">None</option>
            {policyDocs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
          </select>
        </div>

        <div>
          <label className="label">Estimated treatment cost (₹, optional)</label>
          <input type="number" className="input w-48" value={treatmentAmount} onChange={(e) => setTreatmentAmount(e.target.value)} suppressHydrationWarning />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Pre-auth requested at (optional)</label>
            <input type="datetime-local" className="input" value={reqTime} onChange={(e) => setReqTime(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">Insurer responded at (optional)</label>
            <input type="datetime-local" className="input" value={decTime} onChange={(e) => setDecTime(e.target.value)} suppressHydrationWarning />
          </div>
        </div>

        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Checking...</> : "Check this denial"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center gap-2">
            {result.is_valid_denial ? (
              <><CheckCircle2 size={18} style={{ color: "#4ADE80" }} /><span className="text-sm font-semibold" style={{ color: "#4ADE80" }}>Denial reason looks valid</span></>
            ) : (
              <><XCircle size={18} style={{ color: "#F87171" }} /><span className="text-sm font-semibold" style={{ color: "#F87171" }}>Denial reason looks questionable</span></>
            )}
          </div>

          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.denial_reason_summary}</p>

          {result.tat_violated && (
            <div className="rounded-lg p-3" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
              <p className="text-xs font-semibold" style={{ color: "#F87171" }}>Potential TAT non-compliance</p>
              <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{result.tat_violation_detail}</p>
              <p className="text-xs mt-1 italic" style={{ color: "var(--text-tertiary)" }}>
                The timing issue may warrant clarification or grievance escalation. It does not by itself establish that the underlying cashless denial is invalid.
              </p>
            </div>
          )}

          <div className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
            <p className="text-xs font-semibold mb-1" style={{ color: "#A78BFA" }}>Recommended immediate action</p>
            <p className="text-sm" style={{ color: "var(--text-primary)" }}>
              {result.immediate_recommendation?.replace(/_/g, " ")}
            </p>
            {result.reimbursement_path_note && (
              <p className="text-xs mt-2" style={{ color: "var(--text-tertiary)" }}>{result.reimbursement_path_note}</p>
            )}
          </div>

          {result.key_arguments?.length > 0 && (
            <div>
              <p className="text-xs font-semibold mb-1.5" style={{ color: "var(--text-tertiary)" }}>Key arguments</p>
              <ul className="space-y-1">
                {result.key_arguments.map((a: string, i: number) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-secondary)" }}>• {a}</li>
                ))}
              </ul>
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
