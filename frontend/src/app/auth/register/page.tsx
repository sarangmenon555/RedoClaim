"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import toast from "react-hot-toast";
import { ShieldCheck, Loader2, Lock, Cpu, AlertTriangle } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) { toast.error("Password must be at least 8 characters"); return; }
    setLoading(true);
    try {
      const res = await authApi.register(form);
      const meRes = await authApi.me();
      setAuth(meRes.data, res.data);
      toast.success("Account created!");
      router.push("/dashboard");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{background:"var(--surface)"}}>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full blur-[140px] opacity-15 pointer-events-none"
        style={{background:"radial-gradient(circle,#7C3AED,transparent)"}} />

      <div className="w-full max-w-sm relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2.5 mb-4">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)",boxShadow:"0 0 20px rgba(124,58,237,0.4)"}}>
              <ShieldCheck size={18} className="text-white" />
            </div>
            <span className="font-bold text-xl" style={{color:"var(--text-primary)"}}>RedoClaim</span>
          </div>
          <h1 className="text-2xl font-bold" style={{color:"var(--text-primary)"}}>Create your account</h1>
          <p className="text-sm mt-1" style={{color:"var(--text-secondary)"}}>Free forever • Your data stays local</p>
        </div>

        <form onSubmit={handleSubmit} className="card p-7 space-y-4"
          style={{background:"var(--surface-1)",border:"1px solid var(--surface-5)"}}>
          <div>
            <label className="label">Full name</label>
            <input
              className="input"
              placeholder="Ramesh Kumar"
              value={form.full_name}
              onChange={(e) => setForm({...form, full_name: e.target.value})}
              required
              suppressHydrationWarning
            />
          </div>
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
            <label className="label">Phone (optional)</label>
            <input
              className="input"
              placeholder="+91 98765 43210"
              value={form.phone}
              onChange={(e) => setForm({...form, phone: e.target.value})}
              suppressHydrationWarning
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              placeholder="Minimum 8 characters"
              value={form.password}
              onChange={(e) => setForm({...form, password: e.target.value})}
              required
              suppressHydrationWarning
            />
          </div>

          {/* Privacy promises */}
          <div className="rounded-xl p-3 space-y-2"
            style={{background:"var(--surface-2)",border:"1px solid var(--surface-5)"}}>
            {[
              { icon: Lock, color:"#4ADE80", text:"Documents never leave your server" },
              { icon: Cpu,  color:"#22D3EE", text:"AI runs locally — no cloud APIs" },
            ].map(({ icon: Icon, color, text }) => (
              <div key={text} className="flex items-center gap-2 text-xs" style={{color:"var(--text-secondary)"}}>
                <Icon size={12} style={{color}} />{text}
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center py-3"
            suppressHydrationWarning
          >
            {loading ? <><Loader2 size={15} className="animate-spin" /> Creating account...</> : "Create free account"}
          </button>

          <p className="text-center text-sm" style={{color:"var(--text-tertiary)"}}>
            Already have an account?{" "}
            <Link href="/auth/login" style={{color:"#A78BFA"}} className="font-medium hover:text-violet-300 transition">
              Sign in
            </Link>
          </p>
        </form>

        <div className="mt-4 text-xs p-3 rounded-xl"
          style={{background:"rgba(251,191,36,0.06)",border:"1px solid rgba(251,191,36,0.12)",color:"#FCD34D"}}>
          <div className="flex items-start gap-1.5">
            <AlertTriangle size={11} className="mt-0.5 shrink-0" />
            <span>By registering you acknowledge our{" "}
              <Link href="/disclaimer" className="underline">AI Tool Disclaimer</Link>
              {" "}— outputs are not legal advice.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}