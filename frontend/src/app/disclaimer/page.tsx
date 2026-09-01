"use client";
import Link from "next/link";
import { ShieldCheck, AlertTriangle, Scale, ExternalLink, CheckCircle } from "lucide-react";
import { useT } from "@/lib/i18n/useT";

export default function DisclaimerPage() {
  const t = useT();
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
        <span className="text-sm" style={{color:"var(--text-secondary)"}}>{t("disc_page_nav_label")}</span>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        {/* Big warning */}
        <div className="card p-6" style={{background:"rgba(251,191,36,0.07)",borderColor:"rgba(251,191,36,0.25)"}}>
          <div className="flex items-start gap-4">
            <AlertTriangle className="shrink-0 mt-1" size={28} style={{color:"#FBBF24"}} />
            <div>
              <h1 className="text-xl font-bold mb-2" style={{color:"#FCD34D"}}>
                {t("disc_page_title")}
              </h1>
              <p className="text-sm leading-relaxed" style={{color:"#FCD34D",opacity:0.85}}>
                RedoClaim is an AI-powered research and document drafting tool. It is <strong>not a law firm,
                not a licensed insurance advocate, and does not provide legal advice</strong> of any kind.
                Using this tool does not create any attorney-client relationship.
              </p>
            </div>
          </div>
        </div>

        {/* What we are */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <CheckCircle size={18} style={{color:"#4ADE80"}} /> {t("disc_what_we_are")}
          </h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "An AI-assisted research tool to help you understand IRDAI insurance regulations",
              "A document drafting aid that generates starting-point letters for your review",
              "A reference tool that points to relevant IRDAI circulars and consumer rights",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <CheckCircle size={13} className="shrink-0 mt-0.5" style={{color:"#4ADE80"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* What we are not */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold flex items-center gap-2" style={{color:"var(--text-primary)"}}>
            <AlertTriangle size={18} style={{color:"#F87171"}} /> {t("disc_what_we_not")}
          </h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "A substitute for a licensed insurance advocate or legal professional",
              "A guarantee of any particular legal outcome",
              "A source of legally binding or formally verified regulatory information",
              "Responsible for any decisions you make based on its AI-generated output",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <AlertTriangle size={13} className="shrink-0 mt-0.5" style={{color:"#F87171"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* AI limitations */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold" style={{color:"var(--text-primary)"}}>{t("disc_ai_limitations")}</h2>
          <div className="space-y-3 text-sm" style={{color:"var(--text-secondary)"}}>
            <p><strong style={{color:"var(--text-primary)"}}>AI models can hallucinate.</strong> The AI models used by RedoClaim
            can generate plausible-sounding but incorrect regulation citations, wrong dates, fabricated
            clause references, or legally inaccurate arguments. Always verify every citation independently.</p>
            <p><strong style={{color:"var(--text-primary)"}}>OCR can misread documents.</strong> Scanned PDFs, low-quality images, and handwritten
            documents may be misread by the OCR pipeline, leading to incorrect extracted text and wrong analysis.</p>
            <p><strong style={{color:"var(--text-primary)"}}>Regulations change.</strong> IRDAI regulations are updated periodically. The AI's
            knowledge reflects the regulations it was trained on. Always check the current version at{" "}
            <a href="https://irdai.gov.in/home" target="_blank" rel="noopener noreferrer"
              style={{color:"#A78BFA"}} className="underline">https://irdai.gov.in/home</a>.</p>
            <p><strong style={{color:"var(--text-primary)"}}>Every case is different.</strong> Even if a regulation appears to apply to your
            situation, the specific facts of your case, policy wording, and insurer's interpretation may
            affect the outcome. A licensed advocate can assess your specific circumstances.</p>
          </div>
        </div>

        {/* Your responsibilities */}
        <div className="card p-6 space-y-3">
          <h2 className="text-lg font-bold" style={{color:"var(--text-primary)"}}>{t("disc_your_responsibilities")}</h2>
          <ul className="space-y-2 text-sm" style={{color:"var(--text-secondary)"}}>
            {[
              "Read and verify all AI-generated content before acting on it",
              "Check all IRDAI regulation citations at irdai.gov.in before citing them",
              "Correct all errors (names, dates, amounts, policy numbers) in draft letters",
              "Consult a licensed advocate for important legal decisions",
              "Verify deadlines with your insurer — deadline estimates may be inaccurate",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <Scale size={13} className="shrink-0 mt-0.5" style={{color:"#A78BFA"}} />{item}
              </li>
            ))}
          </ul>
        </div>

        {/* Where to get real help */}
        <div className="card p-6 space-y-3" style={{background:"rgba(74,222,128,0.05)",borderColor:"rgba(74,222,128,0.2)"}}>
          <h2 className="text-lg font-bold" style={{color:"var(--text-primary)"}}>{t("disc_get_help_title")}</h2>
          <div className="grid md:grid-cols-2 gap-3">
            {[
              { name: "Bima Bharosa Portal", desc: "File grievances with IRDAI", url: "https://bimabharosa.irdai.gov.in/" },
              { name: "Insurance Ombudsman", desc: "Free resolution up to ₹50 Lakhs", url: "https://www.cioins.co.in/" },
              { name: "e-Jagriti", desc: "Consumer Court online filing", url: "https://e-jagriti.gov.in/" },
              { name: "NALSA", desc: "Free legal aid from Govt of India", url: "https://nalsa.gov.in" },
            ].map(({ name, desc, url }) => (
            <a
            key={name}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 p-3 rounded-lg border transition-all hover:border-green-400/40"
            style={{
              background: "var(--surface-2)",
              borderColor: "rgba(74,222,128,0.15)",
            }}
           >
                <div>
                  <p className="font-medium text-sm" style={{color:"var(--text-primary)"}}>{name}</p>
                  <p className="text-xs" style={{color:"var(--text-tertiary)"}}>{desc}</p>
                </div>
                <ExternalLink size={12} className="mt-0.5 shrink-0 ml-auto" style={{color:"var(--text-tertiary)"}} />
              </a>
            ))}
          </div>
        </div>

        {/* Liability limitation */}
        <div className="card p-5 text-xs leading-relaxed" style={{background:"var(--surface-2)",color:"var(--text-tertiary)"}}>
          <p>
            <strong style={{color:"var(--text-secondary)"}}>Limitation of Liability: </strong> RedoClaim, its developers, and operators provide
            this tool on an &quot;as is&quot; basis without warranties of any kind. We are not liable for any
            loss, damage, or adverse outcome arising from use of or reliance on AI-generated content
            from this platform. Use of this tool constitutes acceptance of these terms.
          </p>
        </div>

        <div className="text-center">
          <Link href="/dashboard" className="btn-primary">
            {t("disc_go_to_dashboard")}
          </Link>
        </div>
      </div>
    </div>
  );
}
