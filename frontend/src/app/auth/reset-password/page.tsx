"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import toast from "react-hot-toast";
import { ShieldCheck, Loader2, Eye, EyeOff } from "lucide-react";

function ResetPasswordForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      toast.error("Missing or invalid reset link. Please request a new one.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      toast.error("Passwords don't match.");
      return;
    }

    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      toast.success("Password reset. Please log in.");
      router.push("/auth/login");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Reset link is invalid or has expired.");
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
          <h1 className="text-2xl font-bold" style={{color:"var(--text-primary)"}}>Choose a new password</h1>
        </div>

        <form onSubmit={handleSubmit} className="card p-7 space-y-4"
          style={{background:"var(--surface-1)",border:"1px solid var(--surface-5)"}}>
          <div>
            <label className="label">New password</label>
            <div className="relative">
              <input
                type={showPwd ? "text" : "password"}
                className="input pr-10"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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

          <div>
            <label className="label">Confirm new password</label>
            <input
              type={showPwd ? "text" : "password"}
              className="input"
              placeholder="Re-enter password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              suppressHydrationWarning
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center mt-2 py-3"
            suppressHydrationWarning>
            {loading ? <><Loader2 size={15} className="animate-spin" /> Resetting...</> : "Reset password"}
          </button>

          <p className="text-center text-sm" style={{color:"var(--text-tertiary)"}}>
            <Link href="/auth/login" className="font-medium transition" style={{color:"#A78BFA"}}>
              Back to login
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
