import Link from "next/link";
import {
  ShieldCheck, ExternalLink, ArrowRight, ArrowDown, AlertTriangle,
  BookOpen, SearchCheck, FolderOpen, Compass, FileText, Building2, Landmark, Scale,
} from "lucide-react";
import SiteFooter from "@/components/landing/SiteFooter";

const GRO_URL = "https://bimabharosa.irdai.gov.in/";
const BIMA_BHAROSA_URL = "https://bimabharosa.irdai.gov.in/";
const IRDAI_POLICYHOLDER_URL = "https://irdai.gov.in/home";
const OMBUDSMAN_URL = "https://www.cioins.co.in/";

const FLOW = [
  { label: "Your problem", icon: FileText, official: false },
  { label: "Understand your documents with RedoClaim", icon: ShieldCheck, official: false },
  { label: "Formal action?", icon: Compass, official: false },
  { label: "Insurer GRO", icon: Building2, official: true },
  { label: "IRDAI Bima Bharosa, where appropriate", icon: Landmark, official: true },
  { label: "Insurance Ombudsman, where applicable", icon: Scale, official: true },
];

const HELP = [
  { icon: BookOpen, title: "Understand", text: "Understand policy wording, exclusions and relevant documents." },
  { icon: SearchCheck, title: "Review", text: "Review information contained in a rejection letter or other claim documents." },
  { icon: FolderOpen, title: "Organise", text: "Identify potentially relevant information and documents." },
  { icon: Compass, title: "Find the Next Channel", text: "Understand where an official grievance or escalation may need to be directed." },
];

const RESOURCES = [
  { name: "IRDAI — Bima Bharosa", desc: "Official grievance registration and tracking.", url: BIMA_BHAROSA_URL },
  { name: "IRDAI — Policyholder Information", desc: "Official insurance and policyholder resources.", url: IRDAI_POLICYHOLDER_URL },
  { name: "Council for Insurance Ombudsmen", desc: "Official information about Ombudsman procedures and eligibility.", url: OMBUDSMAN_URL },
];

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="btn-secondary">
      {children} <ExternalLink size={14} />
    </a>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section className="card p-6 space-y-3">
      <div className="flex items-center gap-3">
        <span
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
          style={{ background: "linear-gradient(135deg,#7C3AED,#4F46E5)" }}
        >
          {n}
        </span>
        <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function OfficialHelpPage() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--surface)" }}>
      <nav
        className="border-b px-4 h-16 flex items-center gap-2 sticky top-0 z-50 backdrop-blur-xl"
        style={{ background: "rgba(10,10,15,0.85)", borderColor: "var(--surface-4)" }}
      >
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg,#7C3AED,#4F46E5)" }}>
          <ShieldCheck size={14} className="text-white" />
        </div>
        <Link href="/" className="font-bold" style={{ color: "var(--text-primary)" }}>RedoClaim</Link>
        <span style={{ color: "var(--surface-5)" }} className="mx-2">|</span>
        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Official Help</span>
      </nav>

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-12 space-y-8">
        {/* Hero */}
        <header className="space-y-4">
          <h1 className="text-3xl font-extrabold" style={{ color: "var(--text-primary)" }}>Official Help</h1>
          <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>
            Need to take formal action regarding an insurance grievance?
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            RedoClaim can help you understand your documents and identify information that may be relevant to your
            situation. It does not replace the official grievance process.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            If you need to make a formal complaint or pursue an escalation, use the appropriate official channels below.
          </p>
        </header>

        {/* Flow */}
        <div className="card p-5" aria-label="Where RedoClaim fits">
          <ol className="flex flex-col items-stretch gap-1">
            {FLOW.map(({ label, icon: Icon, official }, i) => (
              <li key={label} className="flex flex-col items-center gap-1">
                <div
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg border text-sm"
                  style={{
                    background: official ? "rgba(74,222,128,0.06)" : "rgba(139,92,246,0.08)",
                    borderColor: official ? "rgba(74,222,128,0.25)" : "rgba(139,92,246,0.3)",
                    color: "var(--text-primary)",
                  }}
                >
                  <Icon size={16} style={{ color: official ? "#4ADE80" : "#A78BFA" }} />
                  <span className="font-medium">{label}</span>
                </div>
                {i < FLOW.length - 1 && <ArrowDown size={14} style={{ color: "var(--text-tertiary)" }} />}
              </li>
            ))}
          </ol>
          <div className="flex flex-wrap gap-x-5 gap-y-1 mt-4 text-xs" style={{ color: "var(--text-tertiary)" }}>
            <span><span style={{ color: "#A78BFA" }}>■</span> RedoClaim — understanding &amp; support</span>
            <span><span style={{ color: "#4ADE80" }}>■</span> Official institutions — formal grievance &amp; action</span>
          </div>
        </div>

        {/* 1 */}
        <Step n={1} title="Start With Your Insurer">
          <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            Contact your insurer&apos;s Grievance Redressal Officer
          </h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Start by raising your grievance with the insurer through its official grievance-redressal mechanism. Keep
            copies of your complaint, supporting documents and acknowledgement/reference number.
          </p>
          <ExtLink href={GRO_URL}>Find Insurer GRO Details →</ExtLink>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            The appropriate GRO/contact details depend on your insurer.
          </p>
        </Step>

        {/* 2 */}
        <Step n={2} title="If Your Grievance Remains Unresolved">
          <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>IRDAI Bima Bharosa</h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            If your grievance remains unresolved or you are dissatisfied with the insurer&apos;s response, you can
            consider using IRDAI&apos;s Bima Bharosa grievance mechanism.
          </p>
          <ExtLink href={BIMA_BHAROSA_URL}>Open IRDAI Bima Bharosa →</ExtLink>
          <p className="text-xs leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
            Bima Bharosa is an official IRDAI grievance platform. Use the official IRDAI website for the current
            registration, tracking and escalation information.
          </p>
        </Step>

        {/* 3 */}
        <Step n={3} title="Insurance Ombudsman — Where Applicable">
          <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>Consider the Insurance Ombudsman</h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Depending on your circumstances and eligibility, the Insurance Ombudsman may provide another
            grievance-redressal route.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Eligibility and procedural requirements apply, so check the current official requirements before filing.
          </p>
          <ExtLink href={OMBUDSMAN_URL}>Insurance Ombudsman →</ExtLink>
        </Step>

        {/* 4 */}
        <section
          className="card p-6 space-y-3"
          style={{ background: "rgba(251,191,36,0.07)", borderColor: "rgba(251,191,36,0.3)" }}
        >
          <h2 className="text-lg font-bold flex items-center gap-2" style={{ color: "#FCD34D" }}>
            <AlertTriangle size={18} /> Important
          </h2>
          <p className="text-sm font-semibold" style={{ color: "#FCD34D" }}>
            RedoClaim is not an official grievance portal.
          </p>
          <ul className="space-y-1.5 text-sm list-disc pl-5" style={{ color: "#FCD34D", opacity: 0.9 }}>
            <li>It does not file, decide or adjudicate insurance complaints.</li>
            <li>It does not determine whether an insurer has violated regulations.</li>
            <li>It does not guarantee claim approval, reversal or compensation.</li>
          </ul>
          <p className="text-sm font-medium" style={{ color: "#FCD34D" }}>
            For formal action, always use the appropriate official channel.
          </p>
        </section>

        {/* 5 */}
        <section className="space-y-3">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>What RedoClaim Can Help You With</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {HELP.map(({ icon: Icon, title, text }) => (
              <div key={title} className="card p-4 space-y-1.5">
                <div className="flex items-center gap-2">
                  <Icon size={16} style={{ color: "#A78BFA" }} />
                  <h3 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>{title}</h3>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 6 */}
        <section className="space-y-3">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Official Resources</h2>
          <div className="space-y-2">
            {RESOURCES.map(({ name, desc, url }) => (
              <a
                key={name}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="card flex items-center justify-between gap-3 p-4 hover:border-violet-400/40"
              >
                <div>
                  <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>{name}</p>
                  <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{desc}</p>
                </div>
                <ExternalLink size={14} className="shrink-0" style={{ color: "var(--text-tertiary)" }} />
              </a>
            ))}
          </div>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Always use official websites and current instructions when submitting a grievance.
          </p>
        </section>

        {/* 7 */}
        <section className="card-glow card p-6 space-y-3 text-center">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Need Help Understanding Your Documents?</h2>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            You can return to RedoClaim to analyse your policy or claim documents and better understand the information
            before approaching the appropriate official channel.
          </p>
          <Link href="/dashboard" className="btn-primary">
            Back to RedoClaim <ArrowRight size={14} />
          </Link>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
