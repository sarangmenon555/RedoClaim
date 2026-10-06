"use client";
import { useEffect, useState } from "react";
import { claimsApi } from "@/lib/api";
import { Clock, Info, ExternalLink, Zap } from "lucide-react";
import { format, isPast, differenceInDays } from "date-fns";
import type { Claim, TimelineItem } from "@/types";
import Link from "next/link";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { useT } from "@/lib/i18n/useT";

// Events, insurer TATs, eligibility-dependent routes and time limits are shown
// separately. A GRO filing date is an EVENT; the insurer's ~15-day response is a
// TAT owed BY the insurer; no filing deadline is invented for the GRO, the
// Ombudsman window is conditional/indicative, and consumer-law limitation is not
// calculated.
const KIND_COLOR: Record<string, string> = {
  event: "#F87171",
  tat: "#FBBF24",
  conditional: "#A78BFA",
  limitation: "#22D3EE",
  info: "#9CA3AF",
};

function getItems(claim: Claim): TimelineItem[] | null {
  const sla: any = claim.audit_report?.hierarchy_of_evidence?.step1_sla;
  const items = sla?.timeline_items || sla?.deadlines?.timeline_items;
  return Array.isArray(items) && items.length ? items : null;
}

export default function TimelinePage() {
  const t = useT();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    claimsApi.list().then((r) => setClaims(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Insurer's grievance-response TAT passed, or due within 5 days.
  const attentionCount = claims.filter((c) => {
    if (!c.gro_deadline) return false;
    return differenceInDays(new Date(c.gro_deadline), new Date()) <= 5;
  }).length;

  const kindLabel = (k: string) => t(`tl_kind_${k}`);

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{t("tl_title")}</h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{t("tl_subtitle")}</p>
      </div>

      <DisclaimerBanner variant="banner" context="timeline" />

      <div className="card p-5" style={{ background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.15)" }}>
        <p className="text-xs font-semibold mb-3 flex items-center gap-2" style={{ color: "#C4B5FD" }}>
          <Info size={13} /> {t("tl_irdai_timelines")}
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: t("tl_cashless"), value: "1 hour", color: "#22D3EE" },
            { label: t("tl_gro_resolution"), value: "~15 days", color: "#4ADE80" },
            { label: t("tl_final_settlement"), value: "Varies", color: "#FBBF24" },
            { label: t("tl_ombudsman_filing"), value: "1 year*", color: "#A78BFA" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl p-3 text-center" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
              <p className="text-xl font-bold" style={{ color }}>{value}</p>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>{label}</p>
            </div>
          ))}
        </div>
        <p className="text-xs mt-3" style={{ color: "var(--text-tertiary)" }}>{t("tl_ombudsman_footnote")}</p>
      </div>

      {attentionCount > 0 && (
        <div className="rounded-xl p-4 flex items-center gap-3" style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.25)" }}>
          <Zap size={17} style={{ color: "#FBBF24" }} className="shrink-0" />
          <p className="text-sm font-medium" style={{ color: "#FCD34D" }}>
            {attentionCount} claim{attentionCount > 1 ? "s have an" : " has an"} {t("tl_file_immediately")}
          </p>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">{[1, 2].map((i) => <div key={i} className="card shimmer h-48" />)}</div>
      ) : claims.length === 0 ? (
        <div className="card p-14 text-center" style={{ background: "var(--surface-1)" }}>
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ background: "rgba(139,92,246,0.1)", border: "1px solid rgba(139,92,246,0.2)" }}>
            <Clock size={24} style={{ color: "#A78BFA" }} />
          </div>
          <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{t("tl_no_claims_title")}</p>
          <p className="text-sm mt-2 mb-4" style={{ color: "var(--text-secondary)" }}>{t("tl_no_claims_desc")}</p>
          <Link href="/dashboard/auditor" className="btn-primary">{t("tl_audit_rejection_btn")}</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {claims.map((claim) => {
            const items = getItems(claim);
            const gro = claim.gro_deadline ? new Date(claim.gro_deadline) : null;
            const groDue = !!gro && differenceInDays(gro, new Date()) <= 5;
            const insufficient = claim.audit_report?.hierarchy_of_evidence?.step2_regulations?.evidence_assessment?.status === "insufficient";

            return (
              <div key={claim.id} className="card overflow-hidden" style={groDue ? { border: "1px solid rgba(251,191,36,0.4)" } : {}}>
                <div className="p-5 flex items-start justify-between border-b" style={{ borderColor: "var(--surface-4)" }}>
                  <div>
                    <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{claim.insurer_name}</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                      {claim.policy_number || t("tl_policy_unknown")}
                      {claim.claim_amount ? ` · ₹${(claim.claim_amount / 100000).toFixed(1)}L` : ""}
                      {claim.patient_name ? ` · For ${claim.patient_name}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {groDue && <span className="badge-medium">{t("tl_urgent")}</span>}
                    {insufficient
                      ? <span className="badge-medium">{t("tl_insufficient")}</span>
                      : claim.irdai_violation
                        ? <span className="badge-high">{t("tl_ai_violation")}</span>
                        : <span className="badge-low">{t("tl_ai_no_violation")}</span>}
                  </div>
                </div>

                <div className="p-5">
                  {!items ? (
                    <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                      {claim.rejection_date ? `Claim rejected ${format(new Date(claim.rejection_date), "dd MMM yyyy")}. ` : ""}
                      {t("tl_legacy_note")}
                    </p>
                  ) : (
                    <div className="relative pl-8">
                      <div className="absolute left-3 top-2 bottom-2 w-px" style={{ background: "var(--surface-5)" }} />
                      <div className="space-y-5">
                        {items.map((it, i) => {
                          const color = KIND_COLOR[it.kind] || "#9CA3AF";
                          const past = it.date ? isPast(new Date(it.date)) : false;
                          return (
                            <div key={i} className="flex items-start gap-3">
                              <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 -ml-8 mt-0.5" style={{ background: `${color}26`, border: `1px solid ${color}4D` }}>
                                <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                              </div>
                              <div>
                                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                                  {it.label}{" "}
                                  <span className="text-xs font-normal" style={{ color }}>[{kindLabel(it.kind)}]</span>
                                </p>
                                {it.date && (
                                  <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                                    {format(new Date(it.date), "dd MMM yyyy")}
                                    {(it.kind === "tat" || it.kind === "limitation") && past ? ` · ${t("tl_overdue")}` : ""}
                                  </p>
                                )}
                                {it.note && <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>{it.note}</p>}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 mt-5 pt-4 flex-wrap" style={{ borderTop: "1px solid var(--surface-4)" }}>
                    <Link href={`/dashboard/appeals?claim_id=${claim.id}`} className="btn-primary text-xs px-3 py-2">{t("tl_generate_gro")}</Link>
                    <Link href={`/dashboard/claims/${claim.id}`} className="btn-secondary text-xs px-3 py-2">Full timeline & export PDF</Link>
                    {[["IRDAI Portal", "https://igms.irda.gov.in"], ["e-Jagriti", "https://e-jagriti.gov.in"]].map(([label, url]) => (
                      <a key={label} href={url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs px-3 py-2">
                        {label} <ExternalLink size={10} />
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
