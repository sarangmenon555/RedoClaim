"use client";
import { useEffect, useState } from "react";
import { claimsApi, documentsApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import {
  FileSearch, AlertTriangle, FileText, Clock, ArrowRight,
  ShieldCheck, AlertCircle, Heart, Car, TrendingUp, Sparkles,
  Lock, ChevronRight, Bell, User
} from "lucide-react";
import Link from "next/link";
import type { Claim, Document } from "@/types";
import { format } from "date-fns";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";

/* ─── Insurance Category Tabs ─────────────────────────────────────── */
type InsuranceCategory = "health" | "motor" | "life";

const CATEGORIES: {
  id: InsuranceCategory;
  label: string;
  icon: React.ElementType;
  color: string;
  live: boolean;
  accent: string;
}[] = [
  {
    id: "health",
    label: "Health",
    icon: Heart,
    color: "#F87171",
    accent: "rgba(248,113,113,",
    live: true,
  },
  {
    id: "motor",
    label: "Motor",
    icon: Car,
    color: "#60A5FA",
    accent: "rgba(96,165,250,",
    live: true,
  },
  {
    id: "life",
    label: "Life",
    icon: TrendingUp,
    color: "#4ADE80",
    accent: "rgba(74,222,128,",
    live: true,
  },
];

/* ─── Coming Soon Overlay ──────────────────────────────────────────── */
function ComingSoonBadge({ color }: { color: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest"
      style={{
        background: `${color}18`,
        color,
        border: `1px solid ${color}40`,
        letterSpacing: "0.12em",
      }}
    >
      <Lock size={8} />
      Soon
    </span>
  );
}

function LiveBadge() {
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest"
      style={{
        background: "rgba(74,222,128,0.12)",
        color: "#4ADE80",
        border: "1px solid rgba(74,222,128,0.3)",
        letterSpacing: "0.12em",
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full animate-pulse"
        style={{ background: "#4ADE80" }}
      />
      Live
    </span>
  );
}

/* ─── Coming Soon Panel ────────────────────────────────────────────── */
function ComingSoonPanel({
  category,
}: {
  category: (typeof CATEGORIES)[number];
}) {
  const Icon = category.icon;
  return (
    <div
      className="rounded-2xl p-10 flex flex-col items-center justify-center text-center gap-4 min-h-[340px]"
      style={{
        background: `${category.accent}0.04)`,
        border: `1px dashed ${category.accent}0.25)`,
      }}
    >
      {/* Icon ring */}
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-1"
        style={{
          background: `${category.accent}0.1)`,
          border: `1px solid ${category.accent}0.2)`,
          boxShadow: `0 0 40px ${category.accent}0.1)`,
        }}
      >
        <Icon size={34} style={{ color: category.color, opacity: 0.85 }} />
      </div>

      <div>
        <h3
          className="text-xl font-bold mb-1"
          style={{ color: "var(--text-primary)" }}
        >
          {category.label} Insurance
        </h3>
        <p
          className="text-sm max-w-xs mx-auto"
          style={{ color: "var(--text-secondary)" }}
        >
          AI-powered {category.label.toLowerCase()} insurance analysis is being
          built. Policy auditing, claim tracking &amp; appeal drafting — coming
          soon.
        </p>
      </div>

      {/* Feature chips */}
      <div className="flex flex-wrap gap-2 justify-center mt-1">
        {["Policy Analyzer", "Rejection Audit", "Appeal Drafts", "Timeline"].map(
          (f) => (
            <span
              key={f}
              className="text-xs px-3 py-1 rounded-full"
              style={{
                background: `${category.accent}0.06)`,
                color: `${category.color}`,
                border: `1px solid ${category.accent}0.15)`,
              }}
            >
              {f}
            </span>
          )
        )}
      </div>

      {/* Notify CTA */}
      <button
        className="mt-2 flex items-center gap-2 text-sm font-semibold px-5 py-2.5 rounded-xl transition-all duration-150"
        style={{
          background: `${category.accent}0.1)`,
          color: category.color,
          border: `1px solid ${category.accent}0.25)`,
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.background = `${category.accent}0.18)`;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.background = `${category.accent}0.1)`;
        }}
      >
        <Bell size={14} />
        Notify me when live
      </button>
    </div>
  );
}

/* ─── Main Dashboard ───────────────────────────────────────────────── */
export default function DashboardPage() {
  const { user } = useAuthStore();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] =
    useState<InsuranceCategory>("health");

  useEffect(() => {
    Promise.all([
      claimsApi.list().then((r) => setClaims(r.data)).catch(() => {}),
      documentsApi.list().then((r) => setDocuments(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const urgentClaims = claims.filter((c) => {
    if (!c.gro_deadline) return false;
    const d = Math.ceil(
      (new Date(c.gro_deadline).getTime() - Date.now()) / 86400000
    );
    return d >= 0 && d <= 5;
  });

  const stats = [
    {
      label: "Documents",
      value: loading ? "—" : documents.length,
      icon: FileSearch,
      color: "#22D3EE",
      bg: "rgba(34,211,238,0.08)",
      border: "rgba(34,211,238,0.15)",
      href: "/dashboard/documents",
    },
    {
      label: "Claims analyzed",
      value: loading ? "—" : claims.length,
      icon: AlertTriangle,
      color: "#F87171",
      bg: "rgba(248,113,113,0.08)",
      border: "rgba(248,113,113,0.15)",
      href: "/dashboard/auditor",
    },
    {
      label: "Violations found",
      value: loading ? "—" : claims.filter((c) => c.irdai_violation).length,
      icon: ShieldCheck,
      color: "#FBBF24",
      bg: "rgba(251,191,36,0.08)",
      border: "rgba(251,191,36,0.15)",
      href: "/dashboard/auditor",
    },
    {
      label: "Urgent deadlines",
      value: loading ? "—" : urgentClaims.length,
      icon: Clock,
      color: "#4ADE80",
      bg: "rgba(74,222,128,0.08)",
      border: "rgba(74,222,128,0.15)",
      href: "/dashboard/timeline",
    },
  ];

  const quickActions = [
    {
      href: "/dashboard/analyzer",
      label: "Analyze Policy",
      icon: FileSearch,
      color: "#22D3EE",
      desc: "Extract clauses",
    },
    {
      href: "/dashboard/auditor",
      label: "Audit Rejection",
      icon: AlertTriangle,
      color: "#F87171",
      desc: "IRDAI check",
    },
    {
      href: "/dashboard/cis",
      label: "Scan CIS",
      icon: FileText,
      color: "#A78BFA",
      desc: "Inclusions/exclusions",
    },
    {
      href: "/dashboard/appeals",
      label: "Draft Appeal",
      icon: FileText,
      color: "#4ADE80",
      desc: "GRO / Ombudsman",
    },
    {
      href: "/dashboard/e-jagriti",
      label: "e-Jagriti Guide",
      icon: Clock,
      color: "#FBBF24",
      desc: "Consumer Court",
    },
    {
      href: "/dashboard/settings",
      label: "Settings",
      icon: User,
      color: "#f97dcc",
      desc: "Account Settings",
    },
  ];

  const activeCat = CATEGORIES.find((c) => c.id === activeCategory)!;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Welcome ── */}
      <div className="flex items-start justify-between">
        <div>
          <h2
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Hey, {user?.full_name?.split(" ")[0]}
          </h2>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            AI-assisted insurance research
          </p>
        </div>
        <Sparkles
          size={20}
          style={{ color: "#A78BFA", opacity: 0.6, marginTop: 4 }}
        />
      </div>

      {/* ── Disclaimer ── */}
      <DisclaimerBanner variant="banner" context="general" />

      {/* ── Urgent alerts ── */}
      {urgentClaims.length > 0 && (
        <div
          className="rounded-xl p-4 flex items-start gap-3"
          style={{
            background: "rgba(248,113,113,0.08)",
            border: "1px solid rgba(248,113,113,0.2)",
          }}
        >
          <AlertCircle
            size={17}
            style={{ color: "#F87171" }}
            className="shrink-0 mt-0.5"
          />
          <div>
            <p
              className="font-semibold text-sm"
              style={{ color: "#FCA5A5" }}
            >
              Urgent: Upcoming IRDAI Deadlines
            </p>
            {urgentClaims.map((c) => {
              const days = Math.ceil(
                (new Date(c.gro_deadline!).getTime() - Date.now()) / 86400000
              );
              return (
                <p
                  key={c.id}
                  className="text-xs mt-1"
                  style={{ color: "#F87171" }}
                >
                  GRO deadline vs <strong>{c.insurer_name}</strong> —{" "}
                  <strong>
                    {days} day{days !== 1 ? "s" : ""} left
                  </strong>
                </p>
              );
            })}
            <p
              className="text-xs mt-1.5"
              style={{ color: "rgba(248,113,113,0.6)" }}
            >
              ⚠️ AI estimate — verify with insurer
            </p>
            <Link
              href="/dashboard/timeline"
              className="text-xs font-medium mt-1 inline-block"
              style={{ color: "#F87171", textDecoration: "underline" }}
            >
              View Timeline →
            </Link>
          </div>
        </div>
      )}

      {/* ── Insurance Category Switcher ── */}
      <div
        className="card p-1.5"
        style={{
          background: "var(--surface-1)",
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "6px",
        }}
      >
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className="flex flex-col items-center justify-center gap-1.5 py-3 rounded-xl transition-all duration-200 relative"
              style={{
                background: isActive
                  ? `${cat.accent}0.1)`
                  : "transparent",
                border: isActive
                  ? `1px solid ${cat.accent}0.3)`
                  : "1px solid transparent",
                boxShadow: isActive
                  ? `0 0 16px ${cat.accent}0.12)`
                  : "none",
              }}
            >
              <Icon
                size={18}
                style={{
                  color: isActive ? cat.color : "var(--text-tertiary)",
                  transition: "color 0.2s",
                }}
              />
              <span
                className="text-xs font-semibold"
                style={{
                  color: isActive ? cat.color : "var(--text-tertiary)",
                  transition: "color 0.2s",
                }}
              >
                {cat.label}
              </span>
              <div className="absolute top-2 right-2">
                {cat.live ? <LiveBadge /> : <ComingSoonBadge color={cat.color} />}
              </div>
            </button>
          );
        })}
      </div>

      {/* ── Category Content ── */}
      <>
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map(({ label, value, icon: Icon, color, bg, border, href }) => (
              <Link
                key={label}
                href={href}
                className="card p-5 group"
                style={{ transition: "all 0.2s" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor =
                    border.replace("0.15", "0.5");
                  (e.currentTarget as HTMLElement).style.boxShadow = `0 0 20px ${bg.replace("0.08", "0.15")}`;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor =
                    "var(--surface-4)";
                  (e.currentTarget as HTMLElement).style.boxShadow = "";
                }}
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center mb-3"
                  style={{ background: bg, border: `1px solid ${border}` }}
                >
                  <Icon size={16} style={{ color }} />
                </div>
                <div
                  className="text-2xl font-bold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {value}
                </div>
                <div
                  className="text-xs mt-0.5"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  {label}
                </div>
              </Link>
            ))}
          </div>

          {/* Quick actions */}
          <div
            className="card p-5"
            style={{ background: "var(--surface-1)" }}
          >
            <h3
              className="text-sm font-semibold mb-4"
              style={{ color: "var(--text-secondary)" }}
            >
              Quick actions
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {quickActions.map(({ href, label, icon: Icon, color, desc }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 p-3 rounded-xl transition-all duration-150"
                  style={{ border: "1px solid var(--surface-5)" }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.background =
                      "var(--surface-2)";
                    (e.currentTarget as HTMLElement).style.borderColor =
                      "rgba(139,92,246,0.3)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background =
                      "transparent";
                    (e.currentTarget as HTMLElement).style.borderColor =
                      "var(--surface-5)";
                  }}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                    style={{
                      background: `rgba(${
                        color === "#22D3EE"
                          ? "34,211,238"
                          : color === "#F87171"
                          ? "248,113,113"
                          : color === "#A78BFA"
                          ? "167,139,250"
                          : color === "#4ADE80"
                          ? "74,222,128"
                          : "251,191,36"
                      },0.1)`,
                    }}
                  >
                    <Icon size={14} style={{ color }} />
                  </div>
                  <div>
                    <p
                      className="text-xs font-semibold"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {label}
                    </p>
                    <p
                      className="text-xs"
                      style={{ color: "var(--text-tertiary)" }}
                    >
                      {desc}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Recent claims */}
          {claims.length > 0 && (
            <div
              className="card overflow-hidden"
              style={{ background: "var(--surface-1)" }}
            >
              <div
                className="p-5 flex items-center justify-between border-b"
                style={{ borderColor: "var(--surface-4)" }}
              >
                <h3
                  className="text-sm font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  Recent claims
                </h3>
                <Link
                  href="/dashboard/auditor"
                  className="text-xs"
                  style={{ color: "#A78BFA" }}
                >
                  View all →
                </Link>
              </div>
              <div
                className="divide-y"
                style={{ borderColor: "var(--surface-4)" }}
              >
                {claims.slice(0, 5).map((claim) => (
                  <div
                    key={claim.id}
                    className="p-4 flex items-center justify-between transition-colors"
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLElement).style.background =
                        "var(--surface-2)")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLElement).style.background =
                        "transparent")
                    }
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          background: claim.irdai_violation
                            ? "#F87171"
                            : "#4ADE80",
                        }}
                      />
                      <div>
                        <p
                          className="text-sm font-medium"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {claim.insurer_name}
                        </p>
                        <p
                          className="text-xs"
                          style={{ color: "var(--text-tertiary)" }}
                        >
                          {claim.rejection_date
                            ? format(
                                new Date(claim.rejection_date),
                                "dd MMM yyyy"
                              )
                            : "Date unknown"}
                          {claim.claim_amount
                            ? ` • ₹${(claim.claim_amount / 100000).toFixed(1)}L`
                            : ""}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {claim.irdai_violation && (
                        <span className="badge-high">AI: Violation</span>
                      )}
                      <span
                        className="text-xs px-2 py-0.5 rounded-full font-medium"
                        style={{
                          background:
                            claim.status === "rejected"
                              ? "rgba(248,113,113,0.12)"
                              : claim.status === "appealing"
                              ? "rgba(251,191,36,0.12)"
                              : "rgba(74,222,128,0.12)",
                          color:
                            claim.status === "rejected"
                              ? "#FCA5A5"
                              : claim.status === "appealing"
                              ? "#FCD34D"
                              : "#86EFAC",
                        }}
                      >
                        {claim.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!loading && claims.length === 0 && documents.length === 0 && (
            <div
              className="card p-14 text-center"
              style={{ background: "var(--surface-1)" }}
            >
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{
                  background: "rgba(139,92,246,0.1)",
                  border: "1px solid rgba(139,92,246,0.2)",
                }}
              >
                <ShieldCheck size={28} style={{ color: "#A78BFA" }} />
              </div>
              <h3
                className="font-semibold mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Start your research
              </h3>
              <p
                className="text-sm mb-5"
                style={{ color: "var(--text-secondary)" }}
              >
                Upload your insurance policy or rejection letter to begin
              </p>
              <Link href="/dashboard/analyzer" className="btn-primary">
                Upload first document <ArrowRight size={14} />
              </Link>
            </div>
          )}
        </>
    </div>
  );
}