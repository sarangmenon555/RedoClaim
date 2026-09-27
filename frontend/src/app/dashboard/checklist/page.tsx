"use client";
import { useMemo, useState } from "react";
import { ClipboardCheck, AlertCircle } from "lucide-react";
import { CHECKLISTS } from "@/lib/checklist-data";

const INSURANCE_TYPES = [
  { value: "health", label: "Health" },
  { value: "motor", label: "Motor" },
  { value: "life", label: "Life" },
] as const;

const SCENARIOS = [
  { value: "fresh_claim", label: "Filing a fresh claim" },
  { value: "preauth", label: "Cashless pre-authorization" },
  { value: "rejection_appeal", label: "Appealing a rejection" },
  { value: "settlement_dispute", label: "Disputing a settlement" },
] as const;

export default function ChecklistPage() {
  const [insuranceType, setInsuranceType] = useState<string>("health");
  const [scenario, setScenario] = useState<string>("fresh_claim");
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const activeSet = useMemo(
    () => CHECKLISTS.find((c) => c.insuranceType === insuranceType && c.scenario === scenario),
    [insuranceType, scenario]
  );

  const toggle = (doc: string) => setChecked((prev) => ({ ...prev, [doc]: !prev[doc] }));

  const doneCount = activeSet ? activeSet.items.filter((i) => checked[i.document]).length : 0;

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <ClipboardCheck size={22} style={{ color: "#A78BFA" }} /> Document Completeness Checklist
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Gather everything upfront — insurers repeatedly requesting "one more document" over multiple
          rounds is a documented delay tactic. Check this before you submit anything.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <select className="input" value={insuranceType} onChange={(e) => setInsuranceType(e.target.value)} suppressHydrationWarning>
          {INSURANCE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label} Insurance</option>)}
        </select>
        <select className="input" value={scenario} onChange={(e) => setScenario(e.target.value)} suppressHydrationWarning>
          {SCENARIOS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </div>

      {!activeSet ? (
        <div className="card p-6 text-center text-sm" style={{ color: "var(--text-tertiary)", background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          No checklist available yet for this combination — try "Filing a fresh claim" for a general starting point.
        </div>
      ) : (
        <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{activeSet.title}</h3>
            <span className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>{doneCount}/{activeSet.items.length} gathered</span>
          </div>

          <div className="space-y-2">
            {activeSet.items.map((item, i) => (
              <label key={i} className="flex items-start gap-3 rounded-lg p-3 cursor-pointer transition"
                style={{
                  background: checked[item.document] ? "rgba(74,222,128,0.06)" : "var(--surface-2)",
                  border: `1px solid ${checked[item.document] ? "rgba(74,222,128,0.25)" : "var(--surface-5)"}`,
                }}>
                <input
                  type="checkbox"
                  checked={!!checked[item.document]}
                  onChange={() => toggle(item.document)}
                  className="mt-0.5"
                  suppressHydrationWarning
                />
                <div>
                  <p className="text-sm" style={{ color: checked[item.document] ? "var(--text-tertiary)" : "var(--text-primary)", textDecoration: checked[item.document] ? "line-through" : "none" }}>
                    {item.document}
                    {item.critical && (
                      <span className="ml-2 inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                        style={{ background: "rgba(248,113,113,0.12)", color: "#F87171" }}>
                        <AlertCircle size={9} /> COMMONLY DISPUTED
                      </span>
                    )}
                  </p>
                  {item.note && <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>{item.note}</p>}
                </div>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
