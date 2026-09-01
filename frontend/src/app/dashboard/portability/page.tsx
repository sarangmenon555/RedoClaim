"use client";
import { useState, useEffect } from "react";
import { documentsApi, analysisApi } from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowRight, Loader2, Shield, CheckCircle, Info, ExternalLink } from "lucide-react";
import type { Document } from "@/types";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { useT } from "@/lib/i18n/useT";

export default function PortabilityPage() {
  const t = useT();
  const [policyDocs, setPolicyDocs] = useState<Document[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    policyDocumentId: "",
    yearsCovered: "",
    reasonForPorting: "",
  });

  useEffect(() => {
    documentsApi.list().then((r) => {
      setPolicyDocs(r.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done"));
    }).catch(() => {});
  }, []);

  const getGuide = async () => {
    if (!form.policyDocumentId || !form.yearsCovered || !form.reasonForPorting) {
      toast.error("Please fill all fields");
      return;
    }
    setLoading(true);
    try {
      const res = await analysisApi.portabilityGuide({
        policy_document_id: form.policyDocumentId,
        years_covered: parseFloat(form.yearsCovered),
        reason_for_porting: form.reasonForPorting,
      });
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to generate guide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">{t("pr_title")}</h2>
        <p className="style-text-tertiary text-sm mt-1">
          {t("pr_subtitle")}
        </p>
      </div>

      <DisclaimerBanner variant="banner" context="portability" />

      <div className="card p-5 bg-surface-2 border-violet-500/20">
        <div className="flex items-start gap-3">
          <Shield className="text-violet-400 shrink-0" size={18} />
          <div>
            <p className="font-semibold style-text-secondary">{t("pr_rights_title")}</p>
            <ul className="mt-2 space-y-1">
              {[
                t("pr_right_1"),
                t("pr_right_2"),
                t("pr_right_3"),
                t("pr_right_4"),
              ].map((r) => (
                <li key={r} className="text-xs style-text-secondary flex items-start gap-1.5">
                  <CheckCircle size={11} className="mt-0.5 shrink-0" />{r}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card p-6 space-y-4">
        <h3 className="font-semibold style-text-primary">{t("pr_get_guide_title")}</h3>
        <div className="space-y-3">
          {policyDocs.length > 0 ? (
            <div>
              <label className="label">{t("pr_select_policy")}</label>
              <select className="input" value={form.policyDocumentId}
                onChange={(e) => setForm({...form, policyDocumentId: e.target.value})}>
                <option value="">{t("pr_choose_policy")}</option>
                {policyDocs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
              </select>
            </div>
          ) : (
            <div className="bg-surface-2 border border-amber-500\/20 rounded-lg p-3 text-sm text-amber-700">
              {t("pr_upload_first")}
            </div>
          )}
          <div>
            <label className="label">{t("pr_years_covered")}</label>
            <input className="input" type="number" step="0.5" placeholder="e.g. 3.5"
              value={form.yearsCovered} onChange={(e) => setForm({...form, yearsCovered: e.target.value})} />
          </div>
          <div>
            <label className="label">{t("pr_why_porting")}</label>
            <textarea className="input h-20 resize-none"
              placeholder="e.g. My claim was rejected unfairly, high premiums, poor service..."
              value={form.reasonForPorting}
              onChange={(e) => setForm({...form, reasonForPorting: e.target.value})} />
          </div>
          <button onClick={getGuide} disabled={loading} className="btn-primary">
            {loading ? <><Loader2 size={15} className="animate-spin" /> {t("pr_generating")}</> : <>{t("pr_get_guide_btn")} <ArrowRight size={15} /></>}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-5">
            <h3 className="font-semibold style-text-primary mb-3">{t("pr_your_rights")}</h3>
            <ul className="space-y-2">
              {result.key_rights?.map((r: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm style-text-secondary">
                  <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />{r}
                </li>
              ))}
            </ul>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold style-text-primary mb-3">{t("pr_step_process")}</h3>
            <ol className="space-y-2">
              {result.how_to_port?.map((step: string, i: number) => (
                <li key={i} className="flex items-start gap-3 text-sm style-text-secondary">
                  <span className="w-5 h-5 bg-violet-500 text-white rounded-full flex items-center justify-center text-xs font-bold shrink-0">{i + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold style-text-primary mb-3">{t("pr_detailed_guide")}</h3>
            <div className="prose prose-invert prose-sm max-w-none style-text-secondary whitespace-pre-wrap text-sm leading-relaxed">
              {result.portability_guide}
            </div>
          </div>
          <div className="card p-4 bg-surface-2 flex items-center justify-between flex-wrap gap-3">
            <p className="text-sm style-text-secondary">
              <strong>{t("regulation_label")}</strong> {result.regulation}
            </p>
            <a href="https://www.irdai.gov.in" target="_blank" rel="noopener noreferrer"
              className="btn-secondary text-xs px-3 py-1.5">
              {t("pr_irdai_website")} <ExternalLink size={10} />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
