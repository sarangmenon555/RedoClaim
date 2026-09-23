"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { analysisApi, documentsApi, claimsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Calculator, Loader2, AlertTriangle, IndianRupee } from "lucide-react";
import { useT } from "@/lib/i18n/useT";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document, Claim, PayoutEstimate } from "@/types";

function EstimatorPageInner() {
  const t = useT();
  const searchParams = useSearchParams();
  const [docs, setDocs] = useState<Document[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [documentId, setDocumentId] = useState(searchParams.get("doc") || "");
  const [claimId, setClaimId] = useState(searchParams.get("claim") || "");
  const [claimAmount, setClaimAmount] = useState(searchParams.get("amount") || "");
  const [patientAge, setPatientAge] = useState("");
  const [loading, setLoading] = useState(false);
  const [estimate, setEstimate] = useState<PayoutEstimate | null>(null);

  useEffect(() => {
    documentsApi.list().then((res) =>
      setDocs(res.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done"))
    ).catch(() => {});
    claimsApi.list().then((res) => setClaims(res.data)).catch(() => {});
  }, []);

  const runEstimate = async () => {
    const amount = parseFloat(claimAmount);
    if (!documentId) {
      toast.error("Pick a policy document first");
      return;
    }
    if (!amount || amount <= 0) {
      toast.error("Enter a valid claim amount");
      return;
    }
    setLoading(true);
    setEstimate(null);
    try {
      const res = await analysisApi.estimatePayout(
        documentId,
        amount,
        claimId || undefined,
        patientAge ? parseInt(patientAge, 10) : undefined
      );
      setEstimate(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not compute an estimate");
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n: number) =>
    `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{ color: "var(--text-primary)" }}>
      <div>
        <h2 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          {t("nav_estimator")}
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          {t("estimator_subtitle")}
        </p>
      </div>

      <DisclaimerBanner variant="inline" context="general" />

      <div className="card p-5 space-y-4">
        {docs.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
            {t("estimator_no_docs")}
          </p>
        ) : (
          <div className="space-y-1.5">
            <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              {t("estimator_pick_policy")}
            </label>
            <select
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              className="w-full text-sm rounded-lg px-3 py-2"
              style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-primary)" }}
            >
              <option value="">{t("estimator_select")}</option>
              {docs.map((d) => (
                <option key={d.id} value={d.id}>{d.file_name}</option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              {t("estimator_claim_amount")}
            </label>
            <input
              type="number"
              value={claimAmount}
              onChange={(e) => setClaimAmount(e.target.value)}
              placeholder="e.g. 250000"
              className="w-full text-sm rounded-lg px-3 py-2"
              style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-primary)" }}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              {t("estimator_patient_age")}
            </label>
            <input
              type="number"
              value={patientAge}
              onChange={(e) => setPatientAge(e.target.value)}
              placeholder={t("estimator_optional")}
              className="w-full text-sm rounded-lg px-3 py-2"
              style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        {claims.length > 0 && (
          <div className="space-y-1.5">
            <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              {t("estimator_link_claim")}
            </label>
            <select
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="w-full text-sm rounded-lg px-3 py-2"
              style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-primary)" }}
            >
              <option value="">{t("estimator_none")}</option>
              {claims.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.insurer_name} — {c.policy_number || c.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          onClick={runEstimate}
          disabled={loading}
          className="btn-primary text-sm w-full flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Calculator size={14} />}
          {t("estimator_calculate")}
        </button>
      </div>

      {estimate && (
        <div className="card p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{t("estimator_result_label")}</p>
              <p className="text-3xl font-bold flex items-center gap-1" style={{ color: "var(--text-primary)" }}>
                <IndianRupee size={22} />
                {estimate.estimated_payout.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
                {t("estimator_range")}: {fmt(estimate.estimated_payout_range[0])} – {fmt(estimate.estimated_payout_range[1])}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{t("estimator_claimed")}</p>
              <p className="text-lg font-semibold" style={{ color: "var(--text-secondary)" }}>{fmt(estimate.claim_amount)}</p>
            </div>
          </div>

          {estimate.deductions.length > 0 && (
            <div>
              <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-tertiary)" }}>
                {t("estimator_deductions")}
              </p>
              <div className="space-y-1.5">
                {estimate.deductions.map((d, i) => (
                  <div key={i} className="flex items-center justify-between text-sm rounded-lg px-3 py-2" style={{ background: "var(--surface-2)" }}>
                    <span style={{ color: "var(--text-secondary)" }}>{d.reason}</span>
                    <span className="font-medium" style={{ color: "#F87171" }}>−{fmt(d.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {estimate.assumptions.length > 0 && (
            <div>
              <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-tertiary)" }}>
                {t("estimator_assumptions")}
              </p>
              <div className="space-y-2">
                {estimate.assumptions.map((a, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs rounded-lg px-3 py-2" style={{ background: "rgba(245,158,11,0.1)", color: "var(--text-secondary)" }}>
                    <AlertTriangle size={13} className="shrink-0 mt-0.5" style={{ color: "#F59E0B" }} />
                    <span>{a}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs pt-3 border-t" style={{ color: "var(--text-tertiary)", borderColor: "var(--surface-4)" }}>
            {estimate.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}

export default function EstimatorPage() {
  return (
    <Suspense fallback={
      <div className="max-w-3xl flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-violet-400" size={32} />
      </div>
    }>
      <EstimatorPageInner />
    </Suspense>
  );
}
