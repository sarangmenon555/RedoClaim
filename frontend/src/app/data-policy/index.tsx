"use client";
import Link from "next/link";
import { ShieldCheck, Server, Workflow, Globe2, Trash2, KeyRound, Boxes } from "lucide-react";

export default function DataPolicyPage() {
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
        <span className="text-sm" style={{color:"var(--text-secondary)"}}>Data Policy</span>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        {/* Header */}
        <div className="card p-6" style={{background:"rgba(79,70,229,0.07)",borderColor:"rgba(79,70,229,0.25)"}}>
          <div className="flex items-start gap-4">
            <Server className="shrink-0 mt-1" size={28} style={{color:"#818CF8"}} />
            <div>
              <h1 className="text-xl font-bold mb-2" style={{color:"var(--text-primary)"}}>Data Policy</h1>
              <p className="text-sm leading-relaxed" style={{color:"var(--text-secondary)"}}>
                Last updated: September 23, 2026. This Data Policy describes, in technical detail, what data
                RedoClaim stores, where it is processed, how long it is kept, and how it flows through our
                systems. It supplements our Privacy Policy.
              </p>
            </div>
          </div>
        </div>

        {/* Data categories table */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Boxes size={18} style={{color:"#4ADE80"}} /> Data Categories &amp; Storage
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" style={{color:"var(--text-secondary)"}}>
              <thead>
                <tr style={{color:"var(--text-tertiary)"}} className="text-left">
                  <th className="py-2 pr-4 font-medium">Data Type</th>
                  <th className="py-2 pr-4 font-medium">Examples</th>
                  <th className="py-2 font-medium">Storage Location</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Account data", "Name, email, hashed password", "PostgreSQL (Neon)"],
                  ["Claim data", "Policy number, insurer, claim amount, status, rejection reason, IRDAI violation analysis", "PostgreSQL (Neon)"],
                  ["Documents", "Uploaded claim/policy/medical/motor documents", "Object storage"],
                  ["Document embeddings", "Vector representations of document text for retrieval", "Qdrant vector database"],
                  ["Translated reports", "Cached translations of audit reports", "PostgreSQL (Neon), linked to claim"],
                  ["Timeline/deadline data", "GRO and IRDAI deadlines and reminder status", "PostgreSQL (Neon)"],
                ].map(([type, ex, loc]) => (
                  <tr key={type} style={{borderTop:"1px solid var(--surface-4)"}}>
                    <td className="py-2 pr-4">{type}</td>
                    <td className="py-2 pr-4">{ex}</td>
                    <td className="py-2">{loc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Processing flow */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Workflow size={18} style={{color:"#A78BFA"}} /> Data Processing Flow
          </h2>
          <ol className="space-y-2 text-sm list-decimal list-inside" style={{color:"var(--text-secondary)"}}>
            <li>You upload a document, which is stored in object storage.</li>
            <li>The document is processed via OCR to extract text.</li>
            <li>Extracted text is analyzed by our AI/LLM pipeline to identify claim details, IRDAI violations, and generate an audit report.</li>
            <li>Text chunks may be embedded and stored in our vector database to support retrieval-augmented analysis.</li>
            <li>If you request a translation, the relevant report text is sent to our translation provider and cached against your claim.</li>
          </ol>
        </div>

        {/* Cross-border */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Globe2 size={18} style={{color:"#FBBF24"}} /> Cross-Border Data Transfers
          </h2>
          <p className="text-sm" style={{color:"var(--text-secondary)"}}>
            Some of our service providers (AI/LLM providers, cloud hosting, translation services) may process
            data outside your country of residence. Where this occurs, we rely on the provider&apos;s own data
            protection safeguards and contractual commitments.
          </p>
        </div>

        {/* Retention & deletion */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <Trash2 size={18} style={{color:"#F87171"}} /> Data Retention &amp; Deletion
          </h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "Account and claim data is retained while your account is active",
              "Uploaded documents are retained to support your ongoing claim and appeal process",
              "Upon account deletion request, we delete or anonymize your personal data and documents within a reasonable period, except where retention is required by law",
              "Cached translations are deleted when the associated claim is deleted",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <Trash2 size={13} className="shrink-0 mt-0.5" style={{color:"#F87171"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* Access controls & sub-processors */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <KeyRound size={18} style={{color:"#4ADE80"}} /> Access Controls &amp; Sub-processors
          </h2>
          <div className="space-y-3 text-sm" style={{color:"var(--text-secondary)"}}>
            <p>Access to production data is restricted to authorized personnel on a need-to-know basis. Database
            and storage credentials are managed as environment secrets and are not exposed in application code.</p>
            <p>We use the following categories of sub-processors: cloud infrastructure hosting, managed PostgreSQL
            database, object storage, vector database, AI/LLM inference providers, and translation API providers.
            A current list of named sub-processors is available on request.</p>
            <p>In the event of a data breach affecting your personal information, we will notify affected users
            and relevant authorities as required by applicable law.</p>
          </div>
        </div>

        <div className="text-center">
          <Link href="/dashboard" className="btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    </div>
  );
}