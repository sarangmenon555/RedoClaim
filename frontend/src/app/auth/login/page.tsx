"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import toast from "react-hot-toast";
import { ShieldCheck, Loader2, Eye, EyeOff, AlertTriangle, Zap } from "lucide-react";

const DEMO_EMAIL    = "demo@redoclaim.in";
const DEMO_PASSWORD = "RedoClaim@demo2024";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.login(form.email, form.password);
      const meRes = await authApi.me();
      setAuth(meRes.data, res.data);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setDemoLoading(true);
    try {
      const res   = await authApi.login(DEMO_EMAIL, DEMO_PASSWORD);
      const meRes = await authApi.me();
      setAuth(meRes.data, res.data);
      toast.success("Welcome! You're in the demo.");
      router.push("/dashboard");
    } catch {
      toast.error("Demo login failed — please try again.");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{background:"var(--surface)"}}>
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full blur-[140px] opacity-15 pointer-events-none"
        style={{background:"radial-gradient(circle,#7C3AED,transparent)"}} />

      <div className="w-full max-w-sm relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2.5 mb-4">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)",boxShadow:"0 0 20px rgba(124,58,237,0.4)"}}>
              <ShieldCheck size={18} className="text-white" />
            </div>
            <span className="font-bold text-xl" style={{color:"var(--text-primary)"}}>RedoClaim</span>
          </div>
          <h1 className="text-2xl font-bold" style={{color:"var(--text-primary)"}}>Welcome back</h1>
          <p className="text-sm mt-1" style={{color:"var(--text-secondary)"}}>Sign in to your account</p>
        </div>

        {/* ── Try Demo banner ── */}
        <button
          onClick={handleDemo}
          disabled={demoLoading}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm mb-4 transition-all"
          style={{
            background:"linear-gradient(135deg,#4ADE80,#22D3EE)",
            color:"#0a0a0f",
            boxShadow: demoLoading ? "none" : "0 0 20px rgba(74,222,128,0.3)",
          }}
          suppressHydrationWarning>
          {demoLoading
            ? <><Loader2 size={14} className="animate-spin" /> Signing in to demo...</>
            : <><Zap size={14} /> Try Demo — No signup needed</>}
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px" style={{background:"var(--surface-4)"}} />
          <span className="text-xs" style={{color:"var(--text-tertiary)"}}>or sign in with your account</span>
          <div className="flex-1 h-px" style={{background:"var(--surface-4)"}} />
        </div>

        <form onSubmit={handleSubmit} className="card p-7 space-y-4"
          style={{background:"var(--surface-1)",border:"1px solid var(--surface-5)"}}>
          <div>
            <label className="label">Email address</label>
            <input
              type="email"
              className="input"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => setForm({...form, email: e.target.value})}
              required
              suppressHydrationWarning
            />
          </div>
          <div>
            <label className="label">Password</label>
            <div className="relative">
              <input
                type={showPwd ? "text" : "password"}
                className="input pr-10"
                placeholder="Your password"
                value={form.password}
                onChange={(e) => setForm({...form, password: e.target.value})}
                required
                suppressHydrationWarning
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-1/2 -translate-y-1/2 transition"
                style={{color:"var(--text-tertiary)"}}
                suppressHydrationWarning>
                {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center mt-2 py-3"
            suppressHydrationWarning>
            {loading ? <><Loader2 size={15} className="animate-spin" /> Signing in...</> : "Sign in"}
          </button>

          <p className="text-center text-sm" style={{color:"var(--text-tertiary)"}}>
            Don't have an account?{" "}
            <Link href="/auth/register" className="font-medium transition"
              style={{color:"#A78BFA"}}
              onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.color = "#C4B5FD"}
              onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.color = "#A78BFA"}>
              Register free
            </Link>
          </p>
        </form>

        {/* Disclaimer */}
        <div className="mt-4 flex items-start gap-2 text-xs p-3 rounded-xl"
          style={{background:"rgba(251,191,36,0.06)",border:"1px solid rgba(251,191,36,0.12)",color:"#FCD34D"}}>
          <AlertTriangle size={11} className="mt-0.5 shrink-0" />
          AI research tool — outputs are not legal advice.{" "}
          <Link href="/disclaimer" className="underline shrink-0">Disclaimer</Link>
        </div>
      </div>
    </div>
  );
}