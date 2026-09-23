"use client";
import Link from "next/link";
import { ShieldCheck, Lock, Database, Share2, Clock, UserCheck } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen" style={{background:"var(--surface)"}}>
      <nav className="border-b px-4 h-16 flex items-center gap-2 sticky top-0 z-50 backdrop-blur-xl"
        style={{background:"rgba(10,10,15,0.85)",borderColor:"var(--surface-4)"}}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)"}}>
          <ShieldCheck size={14} className="text-white" />
        </div>
        <Link href="/" className="font-bold" style={{color:"var(--text-primary)"}}>RedoClaim</Link>
        <span style={{color:"var(--surface-5)"}} className="mx-2">|</span>
        <span className="text-sm" style={{color:"var(--text-secondary)"}}>Privacy Policy</span>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        {/* Header */}
        <div className="card p-6" style={{background:"rgba(124,58,237,0.07)",borderColor:"rgba(124,58,237,0.25)"}}>
          <div className="flex items-start gap-4">
            <Lock className="shrink-0 mt-1" size={28} style={{color:"#A78BFA"}} />
            <div>
              <h1 className="text-xl font-bold mb-2" style={{color:"var(--text-primary)"}}>Privacy Policy</h1>
              <p className="text-sm leading-relaxed" style={{color:"var(--text-secondary)"}}>
                Last updated: September 23, 2026. RedoClaim (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;) provides a
                platform to help users understand, translate, and appeal insurance claim rejections. This policy
                explains what information we collect, how we use it, and the choices you have.
              </p>
            </div>
          </div>
        </div>

        {/* Information we collect */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Database size={18} style={{color:"#4ADE80"}} /> Information We Collect
          </h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "Account information: name, email address, and login credentials",
              "Insurance and claim information: policy numbers, insurer names, claim amounts, status, rejection reasons, and related dates",
              "Uploaded documents: claim letters, policy documents, medical or motor-related reports, and other files you upload for analysis",
              "Usage data: IP address, device/browser type, and interactions with the platform",
              "Language preference: your selected language for translated reports",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <Database size={13} className="shrink-0 mt-0.5" style={{color:"#4ADE80"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* How we use it */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold" style={{color:"var(--text-primary)"}}>How We Use Your Information</h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "To analyze your claim, extract details via OCR, and generate an audit report of your rejection",
              "To assess potential violations of IRDAI regulations and estimate possible payouts",
              "To translate reports into your preferred language",
              "To generate appeal drafts and track applicable GRO/IRDAI deadlines",
              "To maintain, secure, and improve the platform",
              "To communicate with you about your account or claims",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <UserCheck size={13} className="shrink-0 mt-0.5" style={{color:"#A78BFA"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* Third parties */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Share2 size={18} style={{color:"#F87171"}} /> Third-Party Service Providers
          </h2>
          <p className="text-sm" style={{color:"var(--text-secondary)"}}>
            We use the following categories of third-party services to operate RedoClaim. These providers process
            data on our behalf and are bound by their own privacy and security terms. We do not sell your personal
            information to third parties.
          </p>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "Cloud hosting — for running our application servers",
              "Database hosting (Neon/PostgreSQL) — for storing account, claim, and document metadata",
              "Object storage — for storing uploaded document files",
              "Vector database (Qdrant) — for storing document embeddings used in claim analysis",
              "AI/LLM providers (e.g. Google Gemini, OpenAI) — for document understanding, embeddings, and report generation",
              "Translation services (Sarvam AI) — for generating translated versions of your reports",
              "Background task processing (Celery) — for asynchronous document processing",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <Share2 size={13} className="shrink-0 mt-0.5" style={{color:"#F87171"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* Retention & security */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Clock size={18} style={{color:"#FBBF24"}} /> Data Retention &amp; Security
          </h2>
          <div className="space-y-3 text-sm" style={{color:"var(--text-secondary)"}}>
            <p>We retain your account and claim information for as long as your account is active or as needed to
            provide our services. You may request deletion of your account and associated data at any time.</p>
            <p>We use industry-standard measures, including encryption in transit (TLS), to protect your
            information. However, no method of transmission or storage is completely secure, and we cannot
            guarantee absolute security.</p>
          </div>
        </div>

        {/* Your rights */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold" style={{color:"var(--text-primary)"}}>Your Rights</h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "Access, correct, or update your personal information",
              "Request deletion of your account and data",
              "Withdraw consent for processing, where applicable",
              "Request a copy of the data we hold about you",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <UserCheck size={13} className="shrink-0 mt-0.5" style={{color:"#4ADE80"}} />{item}
              </li>
            ))}
          </ul>
          <p className="text-sm" style={{color:"var(--text-tertiary)"}}>
            Children&apos;s Privacy: RedoClaim is not directed to individuals under 18. We do not knowingly collect
            personal information from children.
          </p>
        </div>

        {/* Policy updates */}
        <div className="card p-5 text-xs leading-relaxed" style={{background:"var(--surface-2)",color:"var(--text-tertiary)"}}>
          <p>
            We may update this Privacy Policy from time to time. Material changes will be communicated via
            the platform.
          </p>
        </div>

        <div className="text-center">
          <Link href="/dashboard" className="btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    </div>
  );
}