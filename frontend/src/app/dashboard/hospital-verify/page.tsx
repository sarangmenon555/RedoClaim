"use client";
import { useState } from "react";
import { networkHospitalsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Monitor, Loader2, CheckCircle2, XCircle, HelpCircle, Plus } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";

const STATUS_META: Record<string, { color: string; icon: any; label: string }> = {
  in_network: { color: "#4ADE80", icon: CheckCircle2, label: "In-network (cashless)" },
  delisted: { color: "#F87171", icon: XCircle, label: "Delisted" },
  unknown: { color: "#9CA3AF", icon: HelpCircle, label: "Unknown / no reports yet" },
};

export default function HospitalVerifyPage() {
  const [insurer, setInsurer] = useState("");
  const [hospital, setHospital] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [showReport, setShowReport] = useState(false);
  const [reportStatus, setReportStatus] = useState("in_network");
  const [reportCity, setReportCity] = useState("");
  const [reportNote, setReportNote] = useState("");
  const [reporting, setReporting] = useState(false);

  const runCheck = async () => {
    if (!insurer.trim() || !hospital.trim()) {
      toast.error("Enter both the insurer and hospital name.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await networkHospitalsApi.check(insurer.trim(), hospital.trim());
      setResult(res.data);
    } catch {
      toast.error("Couldn't check this. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const submitReport = async () => {
    setReporting(true);
    try {
      await networkHospitalsApi.report({
        insurer_name: insurer.trim(),
        hospital_name: hospital.trim(),
        city: reportCity.trim() || undefined,
        status: reportStatus,
        note: reportNote.trim() || undefined,
      });
      toast.success("Thanks — your report helps other users.");
      setShowReport(false);
      setReportNote("");
      runCheck();
    } catch {
      toast.error("Couldn't submit your report.");
    } finally {
      setReporting(false);
    }
  };

  const meta = result ? STATUS_META[result.most_recent_status] : null;
  const Icon = meta?.icon;

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Monitor size={22} style={{ color: "#A78BFA" }} /> Hospital Network Check
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Crowdsourced from other users — check whether a hospital is currently in an insurer's cashless
          network, since insurers change networks and delisting is a common cashless-denial reason.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label">Insurer</label>
            <input className="input" placeholder="e.g. Star Health" value={insurer} onChange={(e) => setInsurer(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">Hospital</label>
            <input className="input" placeholder="e.g. Apollo Hospitals, Chennai" value={hospital} onChange={(e) => setHospital(e.target.value)} suppressHydrationWarning />
          </div>
        </div>
        <button onClick={runCheck} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Checking...</> : "Check network status"}
        </button>
      </div>

      {result && meta && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="flex items-center gap-2.5">
            <Icon size={20} style={{ color: meta.color }} />
            <span className="text-base font-semibold" style={{ color: meta.color }}>{meta.label}</span>
          </div>

          {result.reports.length > 0 ? (
            <div className="space-y-2">
              {result.reports.map((r: any) => (
                <div key={r.id} className="rounded-lg p-3 text-sm" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                  <div className="flex justify-between">
                    <span style={{ color: STATUS_META[r.status]?.color }}>{STATUS_META[r.status]?.label}</span>
                    <span style={{ color: "var(--text-tertiary)" }}>{new Date(r.reported_on).toLocaleDateString()}</span>
                  </div>
                  {r.note && <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{r.note}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
              No one has reported on this insurer + hospital pair yet — be the first.
            </p>
          )}

          {!showReport ? (
            <button onClick={() => setShowReport(true)} className="btn-secondary inline-flex items-center gap-1.5 text-sm px-3 py-2" suppressHydrationWarning>
              <Plus size={14} /> Report current status
            </button>
          ) : (
            <div className="space-y-3 rounded-lg p-4" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
              <select className="input" value={reportStatus} onChange={(e) => setReportStatus(e.target.value)} suppressHydrationWarning>
                <option value="in_network">In-network (cashless works)</option>
                <option value="delisted">Delisted (cashless denied)</option>
              </select>
              <input className="input" placeholder="City (optional)" value={reportCity} onChange={(e) => setReportCity(e.target.value)} suppressHydrationWarning />
              <textarea className="input" placeholder="Note (optional) — e.g. 'confirmed with billing desk, March 2026'"
                value={reportNote} onChange={(e) => setReportNote(e.target.value)} suppressHydrationWarning />
              <div className="flex gap-2">
                <button onClick={submitReport} disabled={reporting} className="btn-primary text-sm px-4 py-2" suppressHydrationWarning>
                  {reporting ? <Loader2 size={14} className="animate-spin" /> : "Submit report"}
                </button>
                <button onClick={() => setShowReport(false)} className="text-sm" style={{ color: "var(--text-tertiary)" }} suppressHydrationWarning>Cancel</button>
              </div>
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
