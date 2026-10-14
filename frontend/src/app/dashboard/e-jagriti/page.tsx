"use client";
import { useState, useEffect } from "react";
import { analysisApi } from "@/lib/api";
import { ExternalLink, CheckCircle, AlertTriangle, Info, Monitor, Scale } from "lucide-react";
import { useT } from "@/lib/i18n/useT";
import { FEE_SLABS, TOP_FEE, consumerFee, consumerForum, formatRupees, slabLabel } from "@/lib/consumer-fees";

export default function EJagritiPage() {
  const t = useT();
  const [guide, setGuide] = useState<any>(null);
  const [premium, setPremium] = useState("");
  const premiumValue = premium.trim() !== "" && Number(premium) >= 0 ? Number(premium) : null;
  const forumKey = premiumValue !== null ? consumerForum(premiumValue) : null;
  const forumName = forumKey ? t(`ej_forum_${forumKey}`) : "";
  const courtFee = premiumValue !== null ? consumerFee(premiumValue) : null;

  useEffect(() => {
    analysisApi.ejagritiGuide().then((r) => setGuide(r.data)).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">{t("ej_title")}</h2>
        <p className="style-text-tertiary text-sm mt-1">
          {t("ej_subtitle")}
        </p>
      </div>

      {/* Trigger banner */}
      <div className="card p-5 bg-surface-2 border-red-500\/20">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-red-600 shrink-0" size={18} />
          <div>
            <p className="font-semibold text-red-800">{t("ej_when_title")}</p>
            <p className="text-sm text-red-700 mt-1">
              {guide?.when_to_use || "If your insurer has not responded within 14 days of your complaint, you can file directly on e-Jagriti Consumer Court portal under Section 2(11) of the Consumer Protection Act, 2019 — Deficiency in Service."}
            </p>
            <div className="flex gap-3 mt-3 flex-wrap">
              <a href="https://e-jagriti.gov.in" target="_blank" rel="noopener noreferrer"
                className="btn-primary text-sm px-4 py-2">
                {t("ej_open_portal")} <ExternalLink size={13} />
              </a>
              <a href="https://bimabharosa.irdai.gov.in/" target="_blank" rel="noopener noreferrer"
                className="btn-secondary text-sm px-4 py-2">
                {t("ej_bima_portal")} <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Legal basis */}
      <div className="card p-5 border-l-4 border-amber-500">
        <div className="flex items-start gap-3">
          <Scale className="text-amber-600 shrink-0" size={18} />
          <div>
            <p className="font-semibold style-text-primary">{t("ej_legal_basis")}</p>
            <p className="text-sm style-text-secondary mt-1">
              <strong>Section 2(11) — Deficiency in Service:</strong> A complaint may allege Deficiency in Service where, for example,
              a claim is alleged to have been rejected without a valid basis, or settlement or grievance response is alleged
              to have been delayed beyond the applicable timeline. Whether a Deficiency in Service is established is decided by the
              Consumer Commission. Relief that may be sought includes the claim amount, interest, and compensation, as the forum may decide.
            </p>
          </div>
        </div>
      </div>

      {/* Forum selection */}
      <div className="card p-5">
        <h3 className="font-semibold style-text-primary mb-1">{t("ej_which_forum")}</h3>
        <p className="text-xs style-text-tertiary mb-4">{t("ej_fee_basis")}</p>
        <div className="space-y-3">
          {[
            { forum: t("ej_forum_district"), amount: "Up to ₹50 lakh", note: t("ej_forum_district_note") },
            { forum: t("ej_forum_state"), amount: "Above ₹50 lakh up to ₹2 crore", note: t("ej_forum_state_note") },
            { forum: t("ej_forum_national"), amount: "Above ₹2 crore", note: t("ej_forum_national_note") },
          ].map(({ forum, amount, note }) => (
            <div key={forum} className="flex items-start gap-3 p-3 bg-surface-2 rounded-lg">
              <div className="w-2 h-2 bg-violet-500 rounded-full mt-1.5 shrink-0" />
              <div>
                <p className="font-medium style-text-primary text-sm">{forum}</p>
                <p className="text-xs text-violet-400">{amount}</p>
                <p className="text-xs style-text-tertiary">{note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold style-text-primary mb-3">{t("ej_fee_title")}</h3>
        <label className="block text-xs style-text-tertiary mb-1">{t("ej_fee_input")}</label>
        <input
          type="number"
          min="0"
          inputMode="numeric"
          value={premium}
          onChange={(e) => setPremium(e.target.value)}
          placeholder="25000"
          className="w-full px-3 py-2 rounded-lg text-sm"
          style={{ background: "var(--surface-2)", border: "1px solid var(--surface-4)", color: "var(--text-primary)" }}
        />
        {premiumValue !== null && courtFee !== null && (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 bg-surface-2 rounded-lg">
              <p className="text-xs style-text-tertiary">{t("ej_fee_forum")}</p>
              <p className="font-medium style-text-primary text-sm">{forumName}</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-lg">
              <p className="text-xs style-text-tertiary">{t("ej_fee_amount")}</p>
              <p className="font-medium style-text-primary text-sm">{courtFee === 0 ? t("ej_fee_nil") : formatRupees(courtFee)}</p>
            </div>
          </div>
        )}
        <details className="mt-4">
          <summary className="text-xs cursor-pointer style-text-secondary">{t("ej_fee_table")}</summary>
          <div className="mt-2 overflow-x-auto rounded-lg" style={{ border: "1px solid var(--surface-4)" }}>
            <table className="w-full text-xs">
              <tbody>
                {FEE_SLABS.map((slab, i) => (
                  <tr key={slabLabel(i)} style={{ borderTop: i === 0 ? "none" : "1px solid var(--surface-4)" }}>
                    <td className="px-3 py-2 style-text-secondary">{slabLabel(i)}</td>
                    <td className="px-3 py-2 text-right style-text-primary">{slab.fee === 0 ? t("ej_fee_nil") : formatRupees(slab.fee)}</td>
                  </tr>
                ))}
                <tr style={{ borderTop: "1px solid var(--surface-4)" }}>
                  <td className="px-3 py-2 style-text-secondary">{slabLabel(FEE_SLABS.length)}</td>
                  <td className="px-3 py-2 text-right style-text-primary">{formatRupees(TOP_FEE)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </div>

      {/* Step-by-step */}
      {guide?.steps && (
        <div className="card p-5">
          <h3 className="font-semibold style-text-primary mb-4 flex items-center gap-2">
            <Monitor size={16} className="text-violet-400" /> {t("ej_step_by_step")}
          </h3>
          <div className="space-y-4">
            {guide.steps.map((s: any) => (
              <div key={s.step} className="flex items-start gap-4">
                <div className="w-8 h-8 bg-violet-500 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">{s.step}</div>
                <div>
                  <p className="font-medium style-text-primary text-sm">{s.action}</p>
                  <p className="text-sm style-text-tertiary mt-0.5">{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relief available */}
      {guide?.relief_you_can_claim && (
        <div className="card p-5">
          <h3 className="font-semibold style-text-primary mb-3">{t("ej_relief")}</h3>
          <ul className="space-y-2">
            {guide.relief_you_can_claim.map((r: string) => (
              <li key={r} className="flex items-start gap-2 text-sm style-text-secondary">
                <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Important notes */}
      {guide?.important_notes && (
        <div className="card p-5 bg-surface-2">
          <div className="flex items-center gap-2 mb-3">
            <Info size={15} className="style-text-tertiary" />
            <h3 className="font-semibold style-text-secondary">{t("ej_important_notes")}</h3>
          </div>
          <ul className="space-y-1.5">
            {guide.important_notes.map((n: string) => (
              <li key={n} className="text-xs style-text-tertiary flex items-start gap-2">
                <span className="w-1 h-1 bg-surface-5 rounded-full mt-1.5 shrink-0" />{n}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
