"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { GitCompare, Loader2 } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

interface ComparisonRow {
  attribute: string;
  values: { document_id: string; file_name: string; display: string }[];
}
interface ExclusionSummary {
  document_id: string;
  file_name: string;
  exclusion_count: number;
  waiting_period_count: number;
  sub_limit_count: number;
}

export default function ComparePoliciesPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ comparison_rows: ComparisonRow[]; exclusion_summary: ExclusionSummary[]; disclaimer: string } | null>(null);

  useEffect(() => {
    documentsApi.list().then((res) =>
      setDocs(res.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done"))
    ).catch(() => {});
  }, []);

  const toggleDoc = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) {
        toast.error("You can compare up to 3 policies at a time.");
        return prev;
      }
      return [...prev, id];
    });
  };

  const runCompare = async () => {
    if (selected.length < 2) {
      toast.error("Select at least 2 policies to compare.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.comparePolicies(selected);
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not compare these policies.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <GitCompare size={22} style={{ color: "#A78BFA" }} /> Compare Policies
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Side-by-side comparison of 2–3 policies you've already uploaded — sum insured, room rent cap,
          co-payment, and PED waiting period, built from clauses already extracted.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <label className="label">Select 2–3 policies</label>
        {docs.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
            Upload and analyze at least two policy documents first.
          </p>
        ) : (
          <div className="space-y-2">
            {docs.map((d) => (
              <label key={d.id} className="flex items-center gap-3 rounded-lg p-3 cursor-pointer"
                style={{
                  background: selected.includes(d.id) ? "rgba(139,92,246,0.1)" : "var(--surface-2)",
                  border: `1px solid ${selected.includes(d.id) ? "rgba(139,92,246,0.35)" : "var(--surface-5)"}`,
                }}>
                <input
                  type="checkbox"
                  checked={selected.includes(d.id)}
                  onChange={() => toggleDoc(d.id)}
                  suppressHydrationWarning
                />
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>{d.file_name}</span>
              </label>
            ))}
          </div>
        )}

        <button onClick={runCompare} disabled={loading || selected.length < 2} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Comparing...</> : `Compare ${selected.length || ""} policies`}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-6 overflow-x-auto" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left pb-3 pr-4" style={{ color: "var(--text-tertiary)" }}>Attribute</th>
                {result.comparison_rows[0]?.values.map((v) => (
                  <th key={v.document_id} className="text-left pb-3 pr-4 font-semibold" style={{ color: "var(--text-primary)" }}>
                    {v.file_name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.comparison_rows.map((row, i) => (
                <tr key={i} style={{ borderTop: "1px solid var(--surface-5)" }}>
                  <td className="py-3 pr-4 font-medium" style={{ color: "var(--text-secondary)" }}>{row.attribute}</td>
                  {row.values.map((v) => (
                    <td key={v.document_id} className="py-3 pr-4" style={{ color: "var(--text-primary)" }}>{v.display}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-tertiary)" }}>Exclusions & sub-limits count</p>
            <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${result.exclusion_summary.length}, minmax(0,1fr))` }}>
              {result.exclusion_summary.map((e) => (
                <div key={e.document_id} className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                  <p className="text-xs font-medium truncate" style={{ color: "var(--text-primary)" }}>{e.file_name}</p>
                  <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
                    {e.exclusion_count} exclusions · {e.waiting_period_count} waiting periods · {e.sub_limit_count} sub-limits
                  </p>
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
