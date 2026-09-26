"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { claimsApi, documentsApi } from "@/lib/api";
import { LayoutDashboard, AlertTriangle, FileText, Users, ChevronRight } from "lucide-react";
import type { Claim, Document } from "@/types";

const STATUS_COLOR: Record<string, string> = {
  filed: "#60A5FA", rejected: "#F87171", appealed: "#FBBF24", resolved: "#4ADE80", pending: "#9CA3AF",
};

export default function PortfolioPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([claimsApi.list(), documentsApi.list()])
      .then(([claimsRes, docsRes]) => {
        setClaims(claimsRes.data);
        setDocs(docsRes.data.filter((d: Document) => d.doc_type === "policy"));
      })
      .finally(() => setLoading(false));
  }, []);

  // Group claims by who they're for — the account holder ("") first, then named family members.
  const grouped = claims.reduce<Record<string, Claim[]>>((acc, c) => {
    const key = c.patient_name || "__self__";
    (acc[key] ||= []).push(c);
    return acc;
  }, {});
  const groupKeys = Object.keys(grouped).sort((a) => (a === "__self__" ? -1 : 1));

  const riskyDocs = docs.filter((d) => (d.risk_flags?.length || 0) > 0);
  const activeClaims = claims.filter((c) => c.status !== "resolved");

  if (loading) {
    return <div className="py-24 text-center" style={{ color: "var(--text-tertiary)" }}>Loading your portfolio...</div>;
  }

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <LayoutDashboard size={22} style={{ color: "#A78BFA" }} /> All My Policies
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Every policy and claim across your account and family members, in one view.
        </p>
      </div>

      {/* Summary tiles */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{docs.length}</p>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Policies on file</p>
        </div>
        <div className="card p-4 text-center" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <p className="text-2xl font-bold" style={{ color: "#FBBF24" }}>{activeClaims.length}</p>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Active claims</p>
        </div>
        <div className="card p-4 text-center" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <p className="text-2xl font-bold" style={{ color: "#F87171" }}>{riskyDocs.length}</p>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Policies with risk flags</p>
        </div>
      </div>

      {/* Policies */}
      <div className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <FileText size={15} /> Policies
        </h3>
        {docs.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>No policy documents uploaded yet.</p>
        ) : (
          <div className="space-y-2">
            {docs.map((d) => (
              <div key={d.id} className="flex items-center justify-between gap-3 rounded-lg p-3"
                style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{d.file_name}</p>
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                    {d.insurance_type?.toUpperCase() || "Unknown type"}
                    {d.extracted_clauses?.renewal_date ? ` · Renews ${d.extracted_clauses.renewal_date}` : ""}
                  </p>
                </div>
                {(d.risk_flags?.length || 0) > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full shrink-0"
                    style={{ background: "rgba(248,113,113,0.1)", color: "#F87171" }}>
                    <AlertTriangle size={11} /> {d.risk_flags!.length} risk flag(s)
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Claims grouped by family member */}
      {groupKeys.map((key) => (
        <div key={key} className="card p-6" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <Users size={15} /> {key === "__self__" ? "Your claims" : `Claims for ${key}`}
          </h3>
          <div className="space-y-2">
            {grouped[key].map((c) => (
              <Link key={c.id} href={`/dashboard/claims/${c.id}`}
                className="flex items-center justify-between gap-3 rounded-lg p-3 transition hover:opacity-80"
                style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{c.insurer_name}</p>
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                    {c.policy_number || "—"} · {c.insurance_type?.toUpperCase()}
                    {c.claim_amount ? ` · ₹${c.claim_amount.toLocaleString("en-IN")}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full"
                    style={{ background: `${STATUS_COLOR[c.status] || "#9CA3AF"}1A`, color: STATUS_COLOR[c.status] || "#9CA3AF" }}>
                    {c.status?.replace("_", " ").toUpperCase()}
                  </span>
                  <ChevronRight size={14} style={{ color: "var(--text-tertiary)" }} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
