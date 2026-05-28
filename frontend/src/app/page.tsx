'use client';
import Link from "next/link";
import {
  ShieldCheck, FileSearch, FileText, Clock,
  ArrowRight, CheckCircle, AlertTriangle, Scale, Zap, Lock, Cpu
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen" style={{background:"var(--surface)"}}>
      {/* Nav */}
      <nav className="border-b sticky top-0 z-50 backdrop-blur-xl"
        style={{background:"rgba(10,10,15,0.85)", borderColor:"var(--surface-4)"}}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)"}}>
              <ShieldCheck size={16} className="text-white" />
            </div>
            <span className="font-bold text-lg" style={{color:"var(--text-primary)"}}>RedoClaim</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium ml-1"
              style={{background:"rgba(251,191,36,0.12)",color:"#FCD34D",border:"1px solid rgba(251,191,36,0.2)"}}>
              AI Powered Insurance Claim Analysis Tool
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="btn-ghost text-sm">Login</Link>
            <Link href="/auth/register" className="btn-primary text-sm">Get Started Free</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Grid bg */}
        <div className="absolute inset-0 grid-bg opacity-30" />
        {/* Violet glow blob */}
        <div className="absolute top-[-100px] left-[50%] translate-x-[-50%] w-[600px] h-[400px] rounded-full blur-[120px] opacity-20"
          style={{background:"radial-gradient(circle,#7C3AED,transparent)"}} />

        <div className="relative max-w-6xl mx-auto px-4 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-8 badge-violet">
            <Cpu size={12} /> 100% local AI • No cloud APIs • Your data stays on your server
          </div>

          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight tracking-tight"
            style={{color:"var(--text-primary)"}}>
            Fight Unfair Insurance<br />
            <span className="gradient-text">Claim Rejections</span>
          </h1>

          <p className="text-lg mb-4 max-w-2xl mx-auto leading-relaxed"
            style={{color:"var(--text-secondary)"}}>
            India's dedicated, fully automated AI research tool for policyholders. 
            Upload your rejection letter — get an IRDAI Master Circular 2024-compliant audit and AI-drafted appeal letters in minutes.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link href="/auth/register" className="btn-primary text-base px-7 py-3">
              Start for free <ArrowRight size={16} />
            </Link>
            <Link href="#features" className="btn-secondary text-base px-7 py-3">
              See features
            </Link>
          </div>
          <p className="mt-4 text-xs" style={{color:"var(--text-tertiary)"}}>
            Local Models • Documents never leave your server
          </p>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y py-8" style={{borderColor:"var(--surface-4)",background:"var(--surface-1)"}}>
        <div className="max-w-6xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[
            { value: "₹50L", label: "Ombudsman claim limit", color: "#A78BFA" },
            { value: "5 yrs", label: "Moratorium period (2024)", color: "#22D3EE" },
            { value: "1 hr", label: "Cashless TAT (IRDAI)", color: "#4ADE80" },
            { value: "30 days", label: "Settlement deadline", color: "#FBBF24" },
          ].map((s) => (
            <div key={s.label}>
              <div className="text-3xl font-bold mb-1" style={{color: s.color}}>{s.value}</div>
              <div className="text-xs" style={{color:"var(--text-tertiary)"}}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-3" style={{color:"var(--text-primary)"}}>
            What RedoClaim does
          </h2>
          <p className="text-sm mb-2" style={{color:"var(--text-secondary)"}}>
            Six AI-assisted research tools — all running locally on your machine
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              icon: FileSearch, label: "Policy Analyzer",
              desc: "Extracts waiting periods, exclusions, sub-limits, room rent caps, and risky clauses from policy PDFs.",
              color: "#22D3EE", bg: "rgba(34,211,238,0.08)", border: "rgba(34,211,238,0.15)",
            },
            {
              icon: FileSearch, label: "CIS Scanner",
              desc: "Scans your Customer Information Sheet — extracts inclusions and exclusions per IRDAI Master Circular 2024, Para 4.2.",
              color: "#A78BFA", bg: "rgba(167,139,250,0.08)", border: "rgba(167,139,250,0.15)",
            },
            {
              icon: AlertTriangle, label: "Rejection Auditor",
              desc: "3-step IRDAI Hierarchy of Evidence audit: SLA violations → Regulatory violations → Redressal route.",
              color: "#F87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.15)",
            },
            {
              icon: FileText, label: "Appeal Drafter",
              desc: "Generates draft GRO letters, Ombudsman complaints, E-Daakhil drafts citing IRDAI regulations.",
              color: "#4ADE80", bg: "rgba(74,222,128,0.08)", border: "rgba(74,222,128,0.15)",
            },
            {
              icon: Clock, label: "Timeline Tracker",
              desc: "Tracks 15-day GRO, 30-day TAT, Ombudsman, and Consumer Court deadlines with alerts.",
              color: "#FBBF24", bg: "rgba(251,191,36,0.08)", border: "rgba(251,191,36,0.15)",
            },
            {
              icon: Scale, label: "Portability Advisor",
              desc: "IRDAI Regulation 17 portability rights — waiting period credits, moratorium transfer, step-by-step guide.",
              color: "#A78BFA", bg: "rgba(167,139,250,0.08)", border: "rgba(167,139,250,0.15)",
            },
          ].map(({ icon: Icon, label, desc, color, bg, border }) => (
            <div key={label} className="card p-5 group"
              style={{background:"var(--surface-1)",transition:"all 0.2s"}}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.borderColor = border.replace("0.15","0.4");
                (e.currentTarget as HTMLElement).style.background = "var(--surface-2)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.borderColor = "var(--surface-4)";
                (e.currentTarget as HTMLElement).style.background = "var(--surface-1)";
              }}>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                style={{background: bg, border:`1px solid ${border}`}}>
                <Icon size={18} style={{color}} />
              </div>
              <h3 className="font-semibold mb-2" style={{color:"var(--text-primary)"}}>{label}</h3>
              <p className="text-sm leading-relaxed mb-3" style={{color:"var(--text-secondary)"}}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why local AI */}
      <section className="border-y py-16" style={{borderColor:"var(--surface-4)",background:"var(--surface-1)"}}>
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-10" style={{color:"var(--text-primary)"}}>
            Why local AI?
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Lock, color: "#4ADE80", title: "Complete privacy", desc: "Your policy documents and medical data never leave your server. No third-party cloud AI sees your data." },
              { icon: Cpu, color: "#22D3EE", title: "Local models", desc: "100% local models." },
              { icon: Zap, color: "#A78BFA", title: "IRDAI knowledge built-in", desc: "RAG pipeline with IRDAI Master Circular 2024, Health Regs 2024, Ombudsman Rules 2017 loaded locally." },
            ].map(({ icon: Icon, color, title, desc }) => (
              <div key={title} className="card p-6 text-center">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{background:`rgba(${color === "#4ADE80" ? "74,222,128" : color === "#22D3EE" ? "34,211,238" : "167,139,250"},0.1)`,border:`1px solid rgba(${color === "#4ADE80" ? "74,222,128" : color === "#22D3EE" ? "34,211,238" : "167,139,250"},0.2)`}}>
                  <Icon size={20} style={{color}} />
                </div>
                <h3 className="font-semibold mb-2" style={{color:"var(--text-primary)"}}>{title}</h3>
                <p className="text-sm leading-relaxed" style={{color:"var(--text-secondary)"}}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold mb-4" style={{color:"var(--text-primary)"}}>
          Start your research today
        </h2>
        <p className="mb-8 max-w-lg mx-auto text-sm" style={{color:"var(--text-secondary)"}}>
          Free, private, and runs entirely on your own machine.
          For legal action, always consult a licensed insurance advocate.
        </p>
        <Link href="/auth/register" className="btn-primary text-base px-8 py-3">
          Get started free <ArrowRight size={16} />
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t py-8" style={{borderColor:"var(--surface-4)",background:"var(--surface-1)"}}>
        <div className="max-w-6xl mx-auto px-4 space-y-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md flex items-center justify-center"
                style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)"}}>
                <ShieldCheck size={12} className="text-white" />
              </div>
              <span className="font-semibold" style={{color:"var(--text-primary)"}}>RedoClaim</span>
              <span style={{color:"var(--text-tertiary)"}}>— AI Powered Insurance Claim Analysis Tool</span>
            </div>
            <div className="flex gap-4 text-xs" style={{color:"var(--text-tertiary)"}}>
              {[
                ["IRDAI","https://irdai.gov.in/home"],
                ["Bima Bharosa","https://bimabharosa.irdai.gov.in/"],
                ["e-Jagriti","https://e-jagriti.gov.in/"],
                ["Disclaimer","/disclaimer"],
              ].map(([label, href]) => (
                <a key={label} href={href} target={href.startsWith("http") ? "_blank" : undefined}
                  rel="noopener noreferrer"
                  className="hover:text-violet-400 transition-colors">{label}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
