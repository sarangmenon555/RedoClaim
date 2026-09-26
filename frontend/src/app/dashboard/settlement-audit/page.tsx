"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { FileSearch, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

export default function SettlementAuditPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [settlementDocId, setSettlementDocId] = useState("");
  const [policyDocId, setPolicyDocId] = useState("");
  const [claimAmount, setClaimAmount] = useState("");
  const [settledAmount, setSettledAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    documentsApi.list().then((res) => setDocs(res.data.filter((d: Document) => d.ocr_status === "done"))).catch(() => {});
  }, []);

  const policyDocs = docs.filter((d) => d.doc_type === "policy");

  const runAudit = async () => {
    if (!settlementDocId || !claimAmount || !settledAmount) {
      toast.error("Fill in the settlement letter, claim amount, and settled amount.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.auditSettlement({
        settlement_document_id: settlementDocId,
        policy_document_id: policyDocId || undefined,
        claim_amount: parseFloat(claimAmount),
        settled_amount: parseFloat(settledAmount),
      });
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not audit this settlement.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <FileSearch size={22} style={{ color: "#A78BFA" }} /> Settlement Second Opinion
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Got paid, but less than you expected? Upload the settlement letter and we'll check whether
          each deduction the insurer made actually matches your policy terms.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div>
          <label className="label">Settlement letter document</label>
          <select className="input" value={settlementDocId} onChange={(e) => setSettlementDocId(e.target.value)} suppressHydrationWarning>
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

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label">Claim amount (₹)</label>
            <input type="number" className="input" value={claimAmount} onChange={(e) => setClaimAmount(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">Amount settled (₹)</label>
            <input type="number" className="input" value={settledAmount} onChange={(e) => setSettledAmount(e.target.value)} suppressHydrationWarning />
          </div>
        </div>

        <button onClick={runAudit} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Auditing...</> : "Audit this settlement"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center gap-2">
            {result.is_settlement_likely_correct ? (
              <><CheckCircle2 size={18} style={{ color: "#4ADE80" }} /><span className="text-sm font-semibold" style={{ color: "#4ADE80" }}>Settlement looks broadly correct</span></>
            ) : (
              <><XCircle size={18} style={{ color: "#F87171" }} /><span className="text-sm font-semibold" style={{ color: "#F87171" }}>Some deductions look questionable</span></>
            )}
          </div>

          {result.total_questionable_deduction > 0 && (
            <div className="rounded-xl p-4 text-center" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Potentially recoverable</p>
              <p className="text-xl font-bold" style={{ color: "#F87171" }}>₹{result.total_questionable_deduction.toLocaleString("en-IN")}</p>
            </div>
          )}

          {result.deductions_reviewed?.length > 0 && (
            <div className="space-y-2">
              {result.deductions_reviewed.map((d: any, i: number) => (
                <div key={i} className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: "var(--text-primary)" }}>{d.stated_reason}</span>
                    <span style={{ color: d.justified_by_policy ? "#4ADE80" : "#F87171" }}>
                      ₹{d.amount_deducted?.toLocaleString("en-IN")} {d.justified_by_policy ? "(justified)" : "(questionable)"}
                    </span>
                  </div>
                  <p className="text-xs mt-1.5" style={{ color: "var(--text-tertiary)" }}>{d.explanation}</p>
                </div>
              ))}
            </div>
          )}

          {result.key_arguments?.length > 0 && (
            <div>
              <p className="text-xs font-semibold mb-1.5" style={{ color: "var(--text-tertiary)" }}>Arguments if disputing</p>
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
