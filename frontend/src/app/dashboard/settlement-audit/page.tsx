"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { FileSearch, Loader2, CheckCircle2, XCircle, AlertTriangle, HelpCircle } from "lucide-react";
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
          {(() => {
            const a: string = result.settlement_assessment ||
              (result.is_settlement_likely_correct === true ? "consistent_with_policy"
                : result.is_settlement_likely_correct === false ? "questionable" : "insufficient_evidence");
            const view =
              a === "consistent_with_policy"
                ? { icon: <CheckCircle2 size={18} style={{ color: "#4ADE80" }} />, color: "#4ADE80", label: "Deductions appear consistent with the supplied policy text" }
              : a === "arithmetic_consistent_scope_unverified"
                ? { icon: <AlertTriangle size={18} style={{ color: "#FBBF24" }} />, color: "#FBBF24", label: "Arithmetic is consistent, but the basis is not verified" }
              : a === "questionable"
                ? { icon: <XCircle size={18} style={{ color: "#F87171" }} />, color: "#F87171", label: "Some deductions look questionable" }
                : { icon: <HelpCircle size={18} style={{ color: "#A78BFA" }} />, color: "#A78BFA", label: "Insufficient evidence to judge this settlement" };
            return (
              <div className="flex items-center gap-2">
                {view.icon}
                <span className="text-sm font-semibold" style={{ color: view.color }}>{view.label}</span>
              </div>
            );
          })()}

          {result.verification_required?.length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.25)" }}>
              <p className="text-xs font-semibold mb-1.5" style={{ color: "#FCD34D" }}>Verify before concluding</p>
              {result.verification_required.map((v: string, i: number) => (
                <p key={i} className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{v}</p>
              ))}
            </div>
          )}

          {result.proportionate_deduction_check?.arithmetic && (
            <div className="rounded-lg p-3 text-xs" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-secondary)" }}>
              <p className="font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Proportionate deduction check</p>
              <p>
                Room rent {"\u20b9"}{result.proportionate_deduction_check.arithmetic.actual_room_rent?.toLocaleString("en-IN")} vs eligible {"\u20b9"}{result.proportionate_deduction_check.arithmetic.eligible_room_rent?.toLocaleString("en-IN")}
                {" "}&rarr; {result.proportionate_deduction_check.arithmetic.deduction_percent}% applied to {"\u20b9"}{result.proportionate_deduction_check.arithmetic.base_amount?.toLocaleString("en-IN")}
                {" "}= {"\u20b9"}{result.proportionate_deduction_check.arithmetic.computed_deduction?.toLocaleString("en-IN")}.
              </p>
              <p className="mt-1">
                Arithmetic matches the insurer: <strong>{String(result.proportionate_deduction_check.arithmetic_consistent)}</strong>
                {" "}&middot; Scope of the deduction established by the policy text: <strong>{result.proportionate_deduction_check.scope_established_in_policy ? "yes" : "no"}</strong>
              </p>
            </div>
          )}

          {result.total_questionable_deduction > 0 && (
            <div className="rounded-xl p-4 text-center" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Potentially recoverable</p>
              <p className="text-xl font-bold" style={{ color: "#F87171" }}>{"\u20b9"}{result.total_questionable_deduction.toLocaleString("en-IN")}</p>
            </div>
          )}

          {result.deductions_reviewed?.length > 0 && (
            <div className="space-y-2">
              {result.deductions_reviewed.map((d: any, i: number) => {
                const status = d.justified_by_policy === true ? { c: "#4ADE80", t: "(consistent with policy text)" }
                  : d.justified_by_policy === false ? { c: "#F87171", t: "(questionable)" }
                  : { c: "#FBBF24", t: "(basis not verified)" };
                return (
                  <div key={i} className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                    <div className="flex justify-between text-sm gap-3">
                      <span style={{ color: "var(--text-primary)" }}>{d.stated_reason}</span>
                      <span className="shrink-0" style={{ color: status.c }}>{"\u20b9"}{d.amount_deducted?.toLocaleString("en-IN")} {status.t}</span>
                    </div>
                    <p className="text-xs mt-1.5" style={{ color: "var(--text-tertiary)" }}>{d.explanation}</p>
                    {(d.policy_evidence?.excerpt || d.policy_evidence?.clause_ref) && (
                      <p className="text-xs mt-1.5 italic" style={{ color: "var(--text-secondary)" }}>
                        Policy evidence: {d.policy_evidence.clause_ref ? `Clause ${d.policy_evidence.clause_ref} \u2014 ` : "clause number not shown \u2014 "}
                        &ldquo;{d.policy_evidence.excerpt}&rdquo;
                        {d.policy_evidence.excerpt_verified === false && " (excerpt not found verbatim in the supplied policy - verify)"}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {result.key_arguments?.length > 0 && (
            <div>
              <p className="text-xs font-semibold mb-1.5" style={{ color: "var(--text-tertiary)" }}>Points to raise with the insurer</p>
              <ul className="space-y-1">
                {result.key_arguments.map((a: string, i: number) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-secondary)" }}>&bull; {a}</li>
                ))}
              </ul>
            </div>
          )}

          {result.citation_check?.unverified?.length > 0 && (
            <p className="text-xs" style={{ color: "#FBBF24" }}>
              Some clause numbers in the AI output could not be found in the supplied policy text and are marked for verification.
            </p>
          )}

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
