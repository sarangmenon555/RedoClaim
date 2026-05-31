"use client";

import { useState, useEffect, useCallback } from "react";

// ─── CONFIG ────────────────────────────────────────────────────────────────
// Set your backend URL in .env.local: NEXT_PUBLIC_API_URL=https://your-api.com
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── TYPES ────────────────────────────────────────────────────────────────
interface Stats {
  users: number;
  documents: number;
  claims: number;
  appeals: number;
  irdai_violations_found: number;
  new_users_7d: number;
  new_users_30d: number;
  active_users: number;
  verified_users: number;
  claim_by_status: Record<string, number>;
  daily_signups: { date: string; count: number }[];
  recent_users: {
    id: string;
    full_name: string;
    email: string;
    created_at: string;
    is_active: boolean;
    is_verified: boolean;
  }[];
}

// ─── MINI SPARKLINE (SVG) ─────────────────────────────────────────────────
function Sparkline({ data }: { data: { date: string; count: number }[] }) {
  if (!data || data.length < 2) return <div style={{ height: 48, color: "var(--color-text-secondary)", fontSize: 12 }}>Not enough data</div>;

  const width = 280;
  const height = 48;
  const max = Math.max(...data.map((d) => d.count), 1);
  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - (d.count / max) * (height - 4) - 2;
    return `${x},${y}`;
  });

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: 48, overflow: "visible" }}>
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke="var(--color-text-info)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Area fill */}
      <polygon
        points={`0,${height} ${pts.join(" ")} ${width},${height}`}
        fill="var(--color-background-info)"
        opacity="0.4"
      />
    </svg>
  );
}

// ─── STAT CARD ─────────────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: number | string;
  sub?: string;
  accent?: "info" | "success" | "warning" | "danger";
}) {
  const bg = accent ? `var(--color-background-${accent})` : "var(--color-background-secondary)";
  const txt = accent ? `var(--color-text-${accent})` : "var(--color-text-primary)";

  return (
    <div
      style={{
        background: bg,
        borderRadius: "var(--border-radius-md)",
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      <span style={{ fontSize: 12, color: accent ? txt : "var(--color-text-secondary)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {label}
      </span>
      <span style={{ fontSize: 28, fontWeight: 500, color: txt, lineHeight: 1 }}>{value}</span>
      {sub && <span style={{ fontSize: 12, color: accent ? txt : "var(--color-text-secondary)", opacity: 0.8 }}>{sub}</span>}
    </div>
  );
}

// ─── BADGE ─────────────────────────────────────────────────────────────────
function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      style={{
        fontSize: 11,
        padding: "2px 7px",
        borderRadius: 20,
        background: ok ? "var(--color-background-success)" : "var(--color-background-danger)",
        color: ok ? "var(--color-text-success)" : "var(--color-text-danger)",
        fontWeight: 500,
      }}
    >
      {label}
    </span>
  );
}

// ─── LOGIN FORM ─────────────────────────────────────────────────────────────
function LoginForm({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const body = new URLSearchParams({ username: email, password });
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Login failed");
      }

      const data = await res.json();

      // Verify the user is an admin before proceeding
      const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const me = await meRes.json();
      if (me.role !== "admin") {
        throw new Error("Access denied. Admin only.");
      }

      localStorage.setItem("admin_token", data.access_token);
      onLogin(data.access_token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    boxSizing: "border-box",
    height: 42,
    padding: "0 12px",
    fontSize: 14,
    color: "#111",
    background: "#fff",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    outline: "none",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f5f4",
      }}
    >
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: "2.5rem 2rem",
          width: "100%",
          maxWidth: 400,
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
        }}
      >
        {/* Logo mark */}
        <div style={{ marginBottom: "1.75rem" }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: "#111",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 16,
            }}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L3 7v11h5v-5h4v5h5V7L10 2z" fill="#fff" />
            </svg>
          </div>
          <h1 style={{ fontSize: 20, fontWeight: 600, margin: 0, color: "#111" }}>RedoClaim Admin</h1>
          <p style={{ fontSize: 14, color: "#6b7280", margin: "4px 0 0" }}>
            Internal dashboard — authorised access only
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#374151" }}>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              style={inputStyle}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#374151" }}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={inputStyle}
            />
          </div>

          {error && (
            <div
              style={{
                fontSize: 13,
                color: "#b91c1c",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 8,
                padding: "8px 12px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: 4,
              height: 42,
              background: loading ? "#6b7280" : "#111",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 500,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.15s",
            }}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── DASHBOARD ─────────────────────────────────────────────────────────────
function Dashboard({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401 || res.status === 403) {
        onLogout();
        return;
      }
      if (!res.ok) throw new Error("Failed to fetch stats");
      const data = await res.json();
      setStats(data);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error loading stats");
    } finally {
      setLoading(false);
    }
  }, [token, onLogout]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const claimStatusColors: Record<string, string> = {
    submitted: "var(--color-background-info)",
    under_review: "var(--color-background-warning)",
    rejected: "var(--color-background-danger)",
    appealing: "var(--color-background-warning)",
    resolved: "var(--color-background-success)",
    escalated: "var(--color-background-danger)",
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-background-tertiary)" }}>
      {/* Header */}
      <div
        style={{
          background: "var(--color-background-primary)",
          borderBottom: "0.5px solid var(--color-border-tertiary)",
          padding: "0 2rem",
          height: 56,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 16, fontWeight: 500 }}>RedoClaim</span>
          <span
            style={{
              fontSize: 11,
              padding: "2px 8px",
              borderRadius: 20,
              background: "var(--color-background-danger)",
              color: "var(--color-text-danger)",
              fontWeight: 500,
            }}
          >
            Admin
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {lastRefresh && (
            <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button onClick={fetchStats} disabled={loading} style={{ fontSize: 13, padding: "6px 14px" }}>
            {loading ? "Refreshing…" : "↻ Refresh"}
          </button>
          <button onClick={onLogout} style={{ fontSize: 13, padding: "6px 14px" }}>
            Sign out
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1.5rem" }}>
        {error && (
          <div
            style={{
              background: "var(--color-background-danger)",
              color: "var(--color-text-danger)",
              borderRadius: "var(--border-radius-md)",
              padding: "0.75rem 1rem",
              marginBottom: "1.5rem",
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        {stats && (
          <>
            {/* Section: Overview */}
            <h2 style={{ fontSize: 14, fontWeight: 500, color: "var(--color-text-secondary)", margin: "0 0 0.75rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Overview
            </h2>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                gap: 12,
                marginBottom: "2rem",
              }}
            >
              <StatCard label="Total users" value={stats.users.toLocaleString()} />
              <StatCard label="New this week" value={stats.new_users_7d} accent="info" sub={`${stats.new_users_30d} this month`} />
              <StatCard label="Active users" value={stats.active_users} sub={`${stats.users > 0 ? Math.round((stats.active_users / stats.users) * 100) : 0}% of total`} />
              <StatCard label="Verified users" value={stats.verified_users} />
              <StatCard label="Total claims" value={stats.claims.toLocaleString()} />
              <StatCard label="IRDAI violations" value={stats.irdai_violations_found} accent={stats.irdai_violations_found > 0 ? "warning" : undefined} />
              <StatCard label="Documents" value={stats.documents.toLocaleString()} />
              <StatCard label="Appeals" value={stats.appeals.toLocaleString()} />
            </div>

            {/* Section: Signups chart + claim status */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 16,
                marginBottom: "2rem",
              }}
            >
              {/* Signups sparkline */}
              <div
                style={{
                  background: "var(--color-background-primary)",
                  border: "0.5px solid var(--color-border-tertiary)",
                  borderRadius: "var(--border-radius-lg)",
                  padding: "1.25rem",
                }}
              >
                <p style={{ margin: "0 0 0.75rem", fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Signups — last 30 days
                </p>
                <Sparkline data={stats.daily_signups} />
                <p style={{ margin: "0.5rem 0 0", fontSize: 12, color: "var(--color-text-secondary)" }}>
                  {stats.daily_signups.length > 0
                    ? `${stats.daily_signups[0].date} → ${stats.daily_signups[stats.daily_signups.length - 1].date}`
                    : "No data"}
                </p>
              </div>

              {/* Claim status breakdown */}
              <div
                style={{
                  background: "var(--color-background-primary)",
                  border: "0.5px solid var(--color-border-tertiary)",
                  borderRadius: "var(--border-radius-lg)",
                  padding: "1.25rem",
                }}
              >
                <p style={{ margin: "0 0 0.75rem", fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Claims by status
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {Object.entries(stats.claim_by_status).map(([status, count]) => (
                    <div key={status} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: claimStatusColors[status] || "var(--color-background-secondary)",
                            border: "1px solid var(--color-border-secondary)",
                          }}
                        />
                        <span style={{ fontSize: 13, textTransform: "capitalize" }}>
                          {status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{count}</span>
                    </div>
                  ))}
                  {Object.keys(stats.claim_by_status).length === 0 && (
                    <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: 0 }}>No claims yet</p>
                  )}
                </div>
              </div>
            </div>

            {/* Section: Recent users */}
            <h2 style={{ fontSize: 14, fontWeight: 500, color: "var(--color-text-secondary)", margin: "0 0 0.75rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Recent registrations
            </h2>
            <div
              style={{
                background: "var(--color-background-primary)",
                border: "0.5px solid var(--color-border-tertiary)",
                borderRadius: "var(--border-radius-lg)",
                overflow: "hidden",
              }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                    {["Name", "Email", "Registered", "Active", "Verified"].map((h) => (
                      <th
                        key={h}
                        style={{
                          textAlign: "left",
                          padding: "0.75rem 1rem",
                          fontWeight: 500,
                          color: "var(--color-text-secondary)",
                          fontSize: 12,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_users.map((user, i) => (
                    <tr
                      key={user.id}
                      style={{
                        borderBottom:
                          i < stats.recent_users.length - 1
                            ? "0.5px solid var(--color-border-tertiary)"
                            : "none",
                      }}
                    >
                      <td style={{ padding: "0.75rem 1rem", fontWeight: 500 }}>{user.full_name}</td>
                      <td style={{ padding: "0.75rem 1rem", color: "var(--color-text-secondary)" }}>
                        {user.email}
                      </td>
                      <td style={{ padding: "0.75rem 1rem", color: "var(--color-text-secondary)" }}>
                        {user.created_at
                          ? new Date(user.created_at).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                            })
                          : "—"}
                      </td>
                      <td style={{ padding: "0.75rem 1rem" }}>
                        <Badge ok={user.is_active} label={user.is_active ? "Active" : "Inactive"} />
                      </td>
                      <td style={{ padding: "0.75rem 1rem" }}>
                        <Badge ok={user.is_verified} label={user.is_verified ? "Verified" : "Unverified"} />
                      </td>
                    </tr>
                  ))}
                  {stats.recent_users.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: "1.5rem 1rem", color: "var(--color-text-secondary)", textAlign: "center" }}>
                        No users yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {loading && !stats && (
          <div style={{ textAlign: "center", paddingTop: "4rem", color: "var(--color-text-secondary)", fontSize: 14 }}>
            Loading…
          </div>
        )}
      </div>
    </div>
  );
}

// ─── PAGE ───────────────────────────────────────────────────────────────────
export default function AdminDashboardPage() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("admin_token");
    if (saved) setToken(saved);
  }, []);

  function handleLogin(t: string) {
    setToken(t);
  }

  function handleLogout() {
    localStorage.removeItem("admin_token");
    setToken(null);
  }

  if (!token) return <LoginForm onLogin={handleLogin} />;
  return <Dashboard token={token} onLogout={handleLogout} />;
}