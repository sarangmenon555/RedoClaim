"use client";
import { useState } from "react";
import { analysisApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Percent, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { ResultActionBar } from "@/components/shared/ResultActionBar";

export default function NcbCheckPage() {
  const [claimFreeYears, setClaimFreeYears] = useState("1");
  const [odPremium, setOdPremium] = useState("");
  const [ncbApplied, setNcbApplied] = useState("");
  const [hadClaim, setHadClaim] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const runCheck = async () => {
    if (!odPremium || !ncbApplied) {
      toast.error("Fill in the OD premium and NCB applied by the insurer.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.ncbCheck({
        claim_free_years: parseInt(claimFreeYears) || 0,
        od_premium_before_ncb: parseFloat(odPremium),
        ncb_applied_by_insurer: parseFloat(ncbApplied),
        had_claim_this_year: hadClaim,
      });
      setResult(res.data);
    } catch {
      toast.error("Couldn't run this check.");
    } finally {
      setLoading(false);
    }
  };

  const emailBody = result
    ? `NCB Check Result\n\nClaim-free years: ${result.claim_free_years}\nExpected NCB: ${result.expected_ncb_percent}%\nApplied by insurer: ${result.ncb_applied_by_insurer}%\nShortfall: Rs.${result.shortfall_amount.toLocaleString("en-IN")}\n\n${result.note}`
    : "";

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Percent size={22} style={{ color: "#A78BFA" }} /> No-Claim Bonus (NCB) Checker
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Check whether your motor renewal quote applies the NCB discount you're actually entitled to,
          against IRDAI's standard NCB slabs.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div>
          <label className="label">Consecutive claim-free years</label>
          <input type="number" min="0" max="5" className="input w-32" value={claimFreeYears} onChange={(e) => setClaimFreeYears(e.target.value)} suppressHydrationWarning />
        </div>

        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-secondary)" }}>
          <input type="checkbox" checked={hadClaim} onChange={(e) => setHadClaim(e.target.checked)} suppressHydrationWarning />
          A claim was made in the immediately preceding year
        </label>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label">OD premium before NCB (₹)</label>
            <input type="number" className="input" value={odPremium} onChange={(e) => setOdPremium(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">NCB % applied by insurer</label>
            <input type="number" className="input" value={ncbApplied} onChange={(e) => setNcbApplied(e.target.value)} suppressHydrationWarning />
          </div>
        </div>

        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Checking...</> : "Check my NCB"}
        </button>
      </div>

      {result && (
        <div id="ncb-result" className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center gap-2">
            {result.is_shortchanged ? (
              <><AlertTriangle size={18} style={{ color: "#F87171" }} /><span className="text-sm font-semibold" style={{ color: "#F87171" }}>You may be under-credited on NCB</span></>
            ) : (
              <><CheckCircle2 size={18} style={{ color: "#4ADE80" }} /><span className="text-sm font-semibold" style={{ color: "#4ADE80" }}>NCB looks correctly applied</span></>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg p-3 text-center" style={{ background: "var(--surface-2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>You're entitled to</p>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{result.expected_ncb_percent}%</p>
            </div>
            <div className="rounded-lg p-3 text-center" style={{ background: "var(--surface-2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Insurer applied</p>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{result.ncb_applied_by_insurer}%</p>
            </div>
          </div>

          {result.is_shortchanged && (
            <div className="rounded-xl p-4 text-center" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Shortfall</p>
              <p className="text-xl font-bold" style={{ color: "#F87171" }}>₹{result.shortfall_amount.toLocaleString("en-IN")}</p>
            </div>
          )}

          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.note}</p>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{result.ncb_is_portable}</p>

          <ResultActionBar emailBody={emailBody} subject="NCB Check Result" printTargetId="ncb-result" />

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
