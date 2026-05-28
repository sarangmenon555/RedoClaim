"use client";
import { useEffect, useState } from "react";
import { claimsApi } from "@/lib/api";
import { Clock, AlertTriangle, CheckCircle, Info, ExternalLink, Zap } from "lucide-react";
import { format, isPast, differenceInDays } from "date-fns";
import type { Claim } from "@/types";
import Link from "next/link";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";

export default function TimelinePage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    claimsApi.list().then((r) => setClaims(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const urgentCount = claims.filter((c) => {
    if (!c.gro_deadline) return false;
    const d = differenceInDays(new Date(c.gro_deadline), new Date());
    return !isPast(new Date(c.gro_deadline)) && d <= 5;
  }).length;

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold" style={{color:"var(--text-primary)"}}>Timeline Tracker</h2>
        <p className="text-sm mt-1" style={{color:"var(--text-secondary)"}}>
          IRDAI mandated deadlines for your claims. AI estimates — verify with your insurer.
        </p>
      </div>

      <DisclaimerBanner variant="banner" context="timeline" />

      {/* IRDAI TAT reference */}
      <div className="card p-5" style={{background:"rgba(139,92,246,0.06)",border:"1px solid rgba(139,92,246,0.15)"}}>
        <p className="text-xs font-semibold mb-3 flex items-center gap-2" style={{color:"#C4B5FD"}}>
          <Info size={13} /> IRDAI Mandated Timelines (Master Circular 2024)
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Cashless approval", value: "1 hour",  color: "#22D3EE" },
            { label: "GRO resolution",    value: "15 days", color: "#4ADE80" },
            { label: "Final settlement",  value: "30 days", color: "#FBBF24" },
            { label: "Ombudsman filing",  value: "1 year",  color: "#A78BFA" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl p-3 text-center"
              style={{background:"var(--surface-2)",border:"1px solid var(--surface-5)"}}>
              <p className="text-xl font-bold" style={{color}}>{value}</p>
              <p className="text-xs mt-0.5" style={{color:"var(--text-tertiary)"}}>{label}</p>
            </div>
          ))}
        </div>
      </div>

      {urgentCount > 0 && (
        <div className="rounded-xl p-4 flex items-center gap-3"
          style={{background:"rgba(248,113,113,0.08)",border:"1px solid rgba(248,113,113,0.2)"}}>
          <Zap size={17} style={{color:"#F87171"}} className="shrink-0" />
          <p className="text-sm font-medium" style={{color:"#FCA5A5"}}>
            {urgentCount} claim{urgentCount > 1 ? "s have" : " has"} a GRO deadline within 5 days. File immediately!
          </p>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1,2].map((i) => <div key={i} className="card shimmer h-48" />)}
        </div>
      ) : claims.length === 0 ? (
        <div className="card p-14 text-center" style={{background:"var(--surface-1)"}}>
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.2)"}}>
            <Clock size={24} style={{color:"#A78BFA"}} />
          </div>
          <p className="font-semibold" style={{color:"var(--text-primary)"}}>No claims tracked yet</p>
          <p className="text-sm mt-2 mb-4" style={{color:"var(--text-secondary)"}}>
            Run a rejection audit to start tracking IRDAI deadlines
          </p>
          <Link href="/dashboard/auditor" className="btn-primary">Audit a Rejection</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {claims.map((claim) => {
            const gro = claim.gro_deadline ? new Date(claim.gro_deadline) : null;
            const groUrgent = gro && !isPast(gro) && differenceInDays(gro, new Date()) <= 5;
            const groPast = gro && isPast(gro);

            return (
              <div key={claim.id} className="card overflow-hidden"
                style={groUrgent ? {border:"1px solid rgba(248,113,113,0.4)",boxShadow:"0 0 20px rgba(248,113,113,0.1)"} : {}}>
                <div className="p-5 flex items-start justify-between border-b"
                  style={{borderColor:"var(--surface-4)"}}>
                  <div>
                    <p className="font-semibold" style={{color:"var(--text-primary)"}}>{claim.insurer_name}</p>
                    <p className="text-xs mt-0.5" style={{color:"var(--text-tertiary)"}}>
                      {claim.policy_number || "Policy unknown"}
                      {claim.claim_amount ? ` • ₹${(claim.claim_amount/100000).toFixed(1)}L` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {groUrgent && <span className="badge-high" style={{animation:"pulse 2s infinite"}}>URGENT</span>}
                    {claim.irdai_violation
                      ? <span className="badge-high">AI: IRDAI Violation</span>
                      : <span className="badge-low">AI: No violation</span>}
                  </div>
                </div>

                <div className="p-5">
                  <div className="relative pl-8">
                    <div className="absolute left-3 top-2 bottom-2 w-px"
                      style={{background:"var(--surface-5)"}} />
                    <div className="space-y-5">
                      {[
                        { label: "Claim rejected", date: claim.rejection_date, color: "#F87171", done: true },
                        { label: "GRO filing deadline (15 days)", date: claim.gro_deadline, color: groUrgent ? "#F87171" : groPast ? "#6B6880" : "#FBBF24", note: groUrgent ? "⚡ File NOW" : groPast ? "Expired" : "Within 15 days of rejection" },
                        { label: "Ombudsman filing", date: claim.irdai_deadline, color: "#A78BFA", note: "Within 45 days of rejection" },
                        { label: "Consumer Court limit", date: claim.rejection_date ? new Date(new Date(claim.rejection_date).getTime() + 2*365*86400000).toISOString() : undefined, color: "#22D3EE", note: "2 years — Consumer Protection Act 2019" },
                      ].map(({ label, date, color, note }, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 -ml-8 mt-0.5"
                            style={{background:`rgba(${color === "#F87171" ? "248,113,113" : color === "#FBBF24" ? "251,191,36" : color === "#A78BFA" ? "167,139,250" : "34,211,238"},0.15)`,border:`1px solid ${color}30`}}>
                            <div className="w-2 h-2 rounded-full" style={{background:color}} />
                          </div>
                          <div>
                            <p className="text-sm font-medium" style={{color:"var(--text-primary)"}}>{label}</p>
                            {date && <p className="text-xs mt-0.5" style={{color:"var(--text-tertiary)"}}>
                              {format(new Date(date), "dd MMM yyyy")}
                            </p>}
                            {note && <p className="text-xs" style={{color}}>{note}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2 mt-5 pt-4 flex-wrap" style={{borderTop:"1px solid var(--surface-4)"}}>
                    <Link href={`/dashboard/appeals?claim_id=${claim.id}`} className="btn-primary text-xs px-3 py-2">
                      Generate GRO Letter
                    </Link>
                    {[
                      ["IRDAI Portal","https://igms.irda.gov.in"],
                      ["E-Daakhil","https://edaakhil.nic.in"],
                    ].map(([label, url]) => (
                      <a key={label} href={url} target="_blank" rel="noopener noreferrer"
                        className="btn-secondary text-xs px-3 py-2">
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
