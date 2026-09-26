"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { AlertTriangle, Loader2, ShieldAlert, CheckCircle2 } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

const SEVERITY_COLOR: Record<string, string> = { high: "#F87171", medium: "#FBBF24", low: "#9CA3AF" };

export default function RenewalCheckPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [oldDocId, setOldDocId] = useState("");
  const [newDocId, setNewDocId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    documentsApi.list().then((res) =>
      setDocs(res.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done"))
    ).catch(() => {});
  }, []);

  const runCheck = async () => {
    if (!oldDocId || !newDocId) {
      toast.error("Select both last year's policy and this year's renewal.");
      return;
    }
    if (oldDocId === newDocId) {
      toast.error("Select two different documents.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.renewalCheck(oldDocId, newDocId);
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not compare these policies.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <AlertTriangle size={22} style={{ color: "#A78BFA" }} /> Renewal Red-Flag Check
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Compare last year's policy against this year's renewal to catch quiet downgrades —
          reduced sum insured, new exclusions, a shrunk room-rent cap, or a disproportionate premium hike.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label">Last year's policy</label>
            <select className="input" value={oldDocId} onChange={(e) => setOldDocId(e.target.value)} suppressHydrationWarning>
              <option value="">Select...</option>
              {docs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">This year's renewal</label>
            <select className="input" value={newDocId} onChange={(e) => setNewDocId(e.target.value)} suppressHydrationWarning>
              <option value="">Select...</option>
              {docs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
            </select>
          </div>
        </div>

        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Comparing...</> : "Check for red flags"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          {result.red_flags?.length > 0 ? (
            <div className="space-y-3">
              {result.red_flags.map((f: any, i: number) => (
                <div key={i} className="rounded-xl p-4" style={{ background: "var(--surface-2)", border: `1px solid ${SEVERITY_COLOR[f.severity]}30` }}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2">
                      <ShieldAlert size={16} className="mt-0.5 shrink-0" style={{ color: SEVERITY_COLOR[f.severity] }} />
                      <div>
                        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{f.field?.replace("_", " ")}</p>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                          {f.old_value} → {f.new_value}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full shrink-0" style={{ background: `${SEVERITY_COLOR[f.severity]}1A`, color: SEVERITY_COLOR[f.severity] }}>
                      {f.severity?.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>{f.explanation}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm" style={{ color: "#4ADE80" }}>
              <CheckCircle2 size={16} /> No adverse changes found in this renewal.
            </div>
          )}

          {result.overall_verdict && (
            <div className="rounded-lg p-4" style={{ background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.15)" }}>
              <p className="text-xs font-semibold mb-1" style={{ color: "#A78BFA" }}>Overall verdict</p>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.overall_verdict}</p>
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
