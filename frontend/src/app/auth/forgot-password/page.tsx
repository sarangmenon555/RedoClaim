"use client";
import { useState } from "react";
import Link from "next/link";
import { authApi } from "@/lib/api";
import toast from "react-hot-toast";
import { ShieldCheck, Loader2, ArrowLeft, MailCheck } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      // Backend always returns a generic success message here, regardless
      // of whether the email is registered — this avoids leaking which
      // emails have accounts (account enumeration).
      setSent(true);
    } catch {
      // Even on an unexpected error, don't reveal anything account-specific.
      toast.error("Something went wrong. Please try again.");
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
          <h1 className="text-2xl font-bold" style={{color:"var(--text-primary)"}}>Reset your password</h1>
          <p className="text-sm mt-1" style={{color:"var(--text-secondary)"}}>
            {sent ? "Check your email for a reset link" : "Enter your email and we'll send you a reset link"}
          </p>
        </div>

        {sent ? (
          <div className="card p-7 space-y-4 text-center"
            style={{background:"var(--surface-1)",border:"1px solid var(--surface-5)"}}>
            <MailCheck size={32} className="mx-auto" style={{color:"#4ADE80"}} />
            <p className="text-sm" style={{color:"var(--text-secondary)"}}>
              If an account exists for <strong>{email}</strong>, a password reset link is on its way.
            </p>
            <Link href="/auth/login" className="btn-primary w-full justify-center py-3 inline-flex">
              <ArrowLeft size={15} /> Back to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="card p-7 space-y-4"
            style={{background:"var(--surface-1)",border:"1px solid var(--surface-5)"}}>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                suppressHydrationWarning
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center mt-2 py-3"
              suppressHydrationWarning>
              {loading ? <><Loader2 size={15} className="animate-spin" /> Sending...</> : "Send reset link"}
            </button>

            <p className="text-center text-sm" style={{color:"var(--text-tertiary)"}}>
              <Link href="/auth/login" className="font-medium transition inline-flex items-center gap-1"
                style={{color:"#A78BFA"}}>
                <ArrowLeft size={13} /> Back to login
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
