"use client";
import { useState } from "react";
import { analysisApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Gauge, Loader2, Plus, Trash2 } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { ResultActionBar } from "@/components/shared/ResultActionBar";

const VERDICT_META: Record<string, { color: string; label: string }> = {
  adequate: { color: "#4ADE80", label: "Adequate" },
  borderline: { color: "#FBBF24", label: "Borderline" },
  likely_inadequate: { color: "#F87171", label: "Likely Inadequate" },
};

export default function SumInsuredCheckPage() {
  const [sumInsured, setSumInsured] = useState("");
  const [cityTier, setCityTier] = useState("metro");
  const [ages, setAges] = useState<string[]>(["35"]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const addMember = () => setAges([...ages, ""]);
  const removeMember = (i: number) => setAges(ages.filter((_, idx) => idx !== i));
  const updateAge = (i: number, value: string) => setAges(ages.map((a, idx) => (idx === i ? value : a)));

  const runCheck = async () => {
    const validAges = ages.filter((a) => a.trim()).map((a) => parseInt(a));
    if (!sumInsured || validAges.length === 0) {
      toast.error("Fill in sum insured and at least one family member's age.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.sumInsuredCheck({
        sum_insured: parseFloat(sumInsured),
        city_tier: cityTier,
        family_members: validAges.map((age) => ({ age })),
      });
      setResult(res.data);
    } catch {
      toast.error("Couldn't run this check.");
    } finally {
      setLoading(false);
    }
  };

  const meta = result ? VERDICT_META[result.verdict] : null;

  const emailBody = result
    ? `Sum Insured Adequacy Check\n\nSum insured: Rs.${result.sum_insured.toLocaleString("en-IN")}\nRecommended minimum: Rs.${result.recommended_minimum.toLocaleString("en-IN")}\nVerdict: ${meta?.label}\n\n${result.headline}`
    : "";

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Gauge size={22} style={{ color: "#A78BFA" }} /> Sum Insured Adequacy Checker
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Check whether your health policy's sum insured is realistically enough for your city and family,
          against typical major-treatment cost benchmarks.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label">Sum insured (₹)</label>
            <input type="number" className="input" value={sumInsured} onChange={(e) => setSumInsured(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">City tier</label>
            <select className="input" value={cityTier} onChange={(e) => setCityTier(e.target.value)} suppressHydrationWarning>
              <option value="metro">Metro (Delhi, Mumbai, Bengaluru, etc.)</option>
              <option value="tier1">Tier 1 (other state capitals, large cities)</option>
              <option value="tier2">Tier 2 (smaller cities/towns)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="label">Family members' ages (covered under this policy)</label>
          <div className="space-y-2">
            {ages.map((age, i) => (
              <div key={i} className="flex gap-2">
                <input type="number" className="input flex-1" placeholder="Age" value={age} onChange={(e) => updateAge(i, e.target.value)} suppressHydrationWarning />
                {ages.length > 1 && (
                  <button onClick={() => removeMember(i)} className="btn-secondary px-3" suppressHydrationWarning><Trash2 size={14} /></button>
                )}
              </div>
            ))}
            <button onClick={addMember} className="btn-secondary text-xs px-3 py-1.5 inline-flex items-center gap-1" suppressHydrationWarning>
              <Plus size={12} /> Add family member
            </button>
          </div>
        </div>

        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Checking...</> : "Check adequacy"}
        </button>
      </div>

      {result && meta && (
        <div id="sum-insured-result" className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <span className="inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full" style={{ background: `${meta.color}1A`, color: meta.color }}>
            {meta.label}
          </span>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.headline}</p>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg p-3 text-center" style={{ background: "var(--surface-2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Your sum insured</p>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>₹{(result.sum_insured / 100000).toFixed(1)}L</p>
            </div>
            <div className="rounded-lg p-3 text-center" style={{ background: "var(--surface-2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Recommended minimum</p>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>₹{(result.recommended_minimum / 100000).toFixed(1)}L</p>
            </div>
          </div>

          <ResultActionBar emailBody={emailBody} subject="Sum Insured Adequacy Check" printTargetId="sum-insured-result" />

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
