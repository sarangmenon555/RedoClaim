import Link from "next/link";
import type { Metadata } from "next";
import HowItWorks from "@/components/landing/HowItWorks";
import SiteFooter from "@/components/landing/SiteFooter";

export const metadata: Metadata = {
  title: "Government & Institutional Review — RedoClaim",
  description:
    "RedoClaim is a free, independent, student-built AI platform seeking expert and institutional guidance for responsible insurance awareness.",
};

const REVIEW_EMAIL = process.env.NEXT_PUBLIC_REVIEW_CONTACT_EMAIL;
const GUARDIAN_EMAIL = process.env.NEXT_PUBLIC_GUARDIAN_CONTACT_EMAIL;
const PROPOSAL_URL = process.env.NEXT_PUBLIC_PROPOSAL_URL;
const PORTFOLIO_URL = process.env.NEXT_PUBLIC_PORTFOLIO_URL;
const GITHUB_URL = process.env.NEXT_PUBLIC_GITHUB_URL;
const LINKEDIN_URL = process.env.NEXT_PUBLIC_LINKEDIN_URL;

const BADGES = [
  { title: "Free To Users", desc: "No charge for accessing RedoClaim" },
  { title: "Student-Built", desc: "Developed by a school student" },
  { title: "Independent", desc: "No government endorsement claimed" },
  { title: "Open To Review", desc: "Seeking expert and institutional feedback" },
];

const REVIEW_AREAS = [
  "Accuracy of insurance-related information",
  "Appropriate use of regulatory sources",
  "Explanation of grievance and escalation pathways",
  "Responsible use of generative AI",
  "Privacy and security of uploaded documents",
  "Multilingual communication",
  "Appropriate disclaimers and limitations",
  "Situations where users should be directed to a human professional or official authority",
];

const ASKS = [
  { title: "Guidance", desc: "Advice on presenting insurance and grievance information accurately and responsibly." },
  { title: "Technical Review", desc: "Feedback from AI, software, cybersecurity, NLP or information-retrieval experts." },
  { title: "Domain Review", desc: "Feedback from insurance, healthcare, consumer-protection or legal professionals." },
  {
    title: "Public-Awareness Collaboration",
    desc: "Exploring whether RedoClaim could serve as an additional voluntary awareness resource, where appropriate.",
  },
  { title: "Pilot Programme", desc: "A small, measurable pilot with a suitable institution, if mutually agreed." },
  {
    title: "Mentorship",
    desc: "Connecting Sarang with experts who can help him improve the project as a student innovator.",
  },
  {
    title: "Direction To The Right Channel",
    desc: "If another department, institution or programme is better suited, guidance toward the appropriate channel.",
  },
];

const DOCUMENTS = [
  "Insurance policy",
  "Customer Information Sheet (CIS)",
  "Claim rejection letter",
  "Other relevant claim documents",
];

const AUDIENCES = [
  {
    title: "Government & Regulators",
    desc: "Insurance, consumer protection, healthcare, digital governance and public-interest technology bodies.",
  },
  {
    title: "Healthcare Institutions",
    desc: "Hospitals, medical colleges, patient-support departments and insurance/TPA desks.",
  },
  { title: "Consumer Organisations", desc: "Consumer-rights and insurance-literacy organisations." },
  {
    title: "Academia",
    desc: "AI/ML, NLP, cybersecurity, law, insurance, healthcare and public-policy researchers.",
  },
  {
    title: "Student Innovation Ecosystem",
    desc: "Schools, innovation programmes, STEM organisations and mentors.",
  },
];

const NOT_ASKED = [
  "Guarantee AI accuracy",
  "Determine whether a claim should be approved",
  "Recommend RedoClaim as a substitute for official procedures",
  "Share patient information with Sarang",
  "Analyse patients' claims",
  "Pay for access",
  "Provide commercial endorsement",
];

const PRINCIPLES = [
  { title: "Independence", desc: "RedoClaim remains independently developed and operated." },
  {
    title: "Transparency",
    desc: "Institutional involvement will not be represented as endorsement unless formally granted.",
  },
  { title: "No Guaranteed Outcomes", desc: "RedoClaim does not promise claim approval, reversal or compensation." },
  {
    title: "Official Pathways First",
    desc: "Users are directed to appropriate insurer, regulatory and grievance mechanisms.",
  },
  {
    title: "Privacy",
    desc: "Institutional partners will not be asked to provide patient or policyholder information for ordinary awareness activities.",
  },
  {
    title: "Human Escalation",
    desc: "Users are directed to appropriate professionals or authorities when human intervention is required.",
  },
];

const PRIVACY_REVIEW = [
  "Document-handling architecture",
  "Data-retention practices",
  "Access controls",
  "Security",
  "Third-party services",
  "AI-processing workflow",
  "Privacy notices",
  "Deletion mechanisms",
];

function SectionHeading({ number, children }: { number: string; children: React.ReactNode }) {
  return (
    <h2 className="text-2xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
      <span style={{ color: "#A78BFA" }}>{number}.</span> {children}
    </h2>
  );
}

function CardGrid({ items, cols = "md:grid-cols-2" }: { items: { title: string; desc: string }[]; cols?: string }) {
  return (
    <div className={`grid gap-4 ${cols}`}>
      {items.map((item) => (
        <div key={item.title} className="card p-5" style={{ background: "var(--surface-1)" }}>
          <h3 className="font-semibold mb-2" style={{ color: "var(--text-primary)" }}>{item.title}</h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{item.desc}</p>
        </div>
      ))}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2 text-sm" style={{ color: "var(--text-secondary)" }}>
      {items.map((item) => (
        <li key={item} className="flex items-start gap-2.5">
          <span className="mt-2 w-1.5 h-1.5 rounded-full shrink-0" style={{ background: "#A78BFA" }} />
          {item}
        </li>
      ))}
    </ul>
  );
}

export default function InstitutionalReviewPage() {
  const demoHref = REVIEW_EMAIL
    ? `mailto:${REVIEW_EMAIL}?subject=${encodeURIComponent("RedoClaim Demonstration Request")}`
    : null;
  const guardianHref = GUARDIAN_EMAIL
    ? `mailto:${GUARDIAN_EMAIL}?subject=${encodeURIComponent("RedoClaim Institutional Enquiry")}`
    : null;
  const profileLinks = [
    ["Portfolio", PORTFOLIO_URL],
    ["GitHub", GITHUB_URL],
    ["LinkedIn", LINKEDIN_URL],
  ].filter((l): l is [string, string] => Boolean(l[1]));

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <nav
        className="border-b px-4 h-16 flex items-center gap-2 sticky top-0 z-50 backdrop-blur-xl"
        style={{ background: "rgba(10,10,15,0.85)", borderColor: "var(--surface-4)" }}
      >
        <Link href="/" className="font-bold" style={{ color: "var(--text-primary)" }}>RedoClaim</Link>
        <span style={{ color: "var(--surface-5)" }} className="mx-2">|</span>
        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Institutional Review</span>
      </nav>

      <header className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-30" />
        <div className="relative max-w-4xl mx-auto px-4 pt-16 pb-12 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight tracking-tight gradient-text">
            Government & Institutional Review
          </h1>
          <p className="text-lg mb-6 max-w-2xl mx-auto" style={{ color: "var(--text-primary)" }}>
            A student-led initiative seeking expert guidance for responsible insurance awareness
          </p>
          <p className="text-sm leading-relaxed max-w-3xl mx-auto mb-8" style={{ color: "var(--text-secondary)" }}>
            RedoClaim is a free, independent AI-powered platform developed by Sarang Menon, a Class 10 student from
            Keralam, to help Indian policyholders better understand insurance policy documents, claim-rejection
            information and possible next steps. The project is being developed as a public-interest technology
            initiative. Sarang welcomes review and guidance from regulators, government bodies, consumer organisations,
            healthcare institutions, academics and insurance professionals to help make RedoClaim more accurate,
            responsible, accessible and useful.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
            {BADGES.map((b) => (
              <div key={b.title} className="card p-4 text-left" style={{ background: "var(--surface-1)" }}>
                <p className="text-sm font-semibold mb-1" style={{ color: "#C4B5FD" }}>{b.title}</p>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-tertiary)" }}>{b.desc}</p>
              </div>
            ))}
          </div>

          <div
            className="card p-5 text-sm leading-relaxed"
            style={{ background: "rgba(139,92,246,0.08)", borderColor: "rgba(139,92,246,0.3)", color: "var(--text-primary)" }}
          >
            We welcome the opportunity for institutions and experts to review RedoClaim, share their guidance, and help
            us continually improve its accuracy, responsibility and usefulness.
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 pb-16 space-y-16">
        <section>
          <SectionHeading number="1">Our Objective</SectionHeading>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            RedoClaim&apos;s objective is to improve insurance awareness and access to understandable information. It is
            not intended to determine whether an insurer is legally right or wrong, guarantee a claim outcome, or replace
            any official grievance or regulatory mechanism.
          </p>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            RedoClaim aims to help a policyholder move from:
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="card p-5" style={{ background: "var(--surface-1)" }}>
              <p className="text-sm italic leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                &ldquo;My claim was rejected. I don&apos;t understand why or what I can do.&rdquo;
              </p>
            </div>
            <div className="card p-5" style={{ background: "var(--surface-1)", borderColor: "rgba(74,222,128,0.25)" }}>
              <p className="text-sm italic leading-relaxed" style={{ color: "var(--text-primary)" }}>
                &ldquo;I understand what my documents say, I know what information may be relevant, and I know where to
                seek appropriate further assistance.&rdquo;
              </p>
            </div>
          </div>
        </section>

        <section>
          <SectionHeading number="2">Why Institutional Review Matters</SectionHeading>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            Insurance claims can involve policy wording, exclusions, waiting periods, Customer Information Sheets, claim
            documentation, regulatory requirements and formal grievance procedures. Because RedoClaim operates in this
            sensitive area, we actively welcome scrutiny and feedback from relevant institutions and professionals.
          </p>
          <p className="text-sm font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            We particularly welcome independent guidance regarding:
          </p>
          <BulletList items={REVIEW_AREAS} />
        </section>

        <section>
          <SectionHeading number="3">What We Are Asking Institutions For</SectionHeading>
          <CardGrid items={ASKS} cols="md:grid-cols-2 lg:grid-cols-3" />
        </section>

        <section>
          <SectionHeading number="4">How RedoClaim Works</SectionHeading>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            A policyholder can provide relevant documents such as:
          </p>
          <div className="mb-4"><BulletList items={DOCUMENTS} /></div>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            RedoClaim uses a Retrieval-Augmented Generation (RAG) approach to analyse user-provided documents alongside
            its curated insurance and regulatory knowledge base. The objective is to produce understandable,
            source-supported information rather than a generic AI response.
          </p>
          <div
            className="card p-5"
            style={{ background: "rgba(251,191,36,0.07)", borderColor: "rgba(251,191,36,0.25)" }}
          >
            <h3 className="font-semibold mb-2" style={{ color: "#FCD34D" }}>AI Is Not The Final Authority</h3>
            <p className="text-sm leading-relaxed" style={{ color: "#FCD34D", opacity: 0.85 }}>
              RedoClaim&apos;s output should be treated as AI-assisted information and analysis, not as a definitive
              legal, regulatory or insurance determination. Users should verify important information through the
              relevant insurer, IRDAI, Insurance Ombudsman where applicable, or an appropriate qualified professional.
            </p>
          </div>
        </section>

        <div className="-mx-4">
          <HowItWorks title="The Six-Step Process" />
        </div>

        <section>
          <SectionHeading number="5">Privacy, Safety & Responsible Use</SectionHeading>
          <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
            Insurance documents may contain sensitive personal, financial and health information. Responsible handling of
            such information is therefore a core consideration in RedoClaim&apos;s development.
          </p>
          <p className="text-sm font-medium mb-3" style={{ color: "var(--text-primary)" }}>
            We welcome independent review of our:
          </p>
          <div className="mb-5"><BulletList items={PRIVACY_REVIEW} /></div>
          <div className="flex gap-4 text-sm flex-wrap">
            <Link href="/privacy-policy" className="underline" style={{ color: "#A78BFA" }}>Privacy Policy</Link>
            <Link href="/data-policy" className="underline" style={{ color: "#A78BFA" }}>Data Policy</Link>
            <Link href="/disclaimer" className="underline" style={{ color: "#A78BFA" }}>Disclaimer</Link>
          </div>
        </section>

        <section>
          <SectionHeading number="6">Multilingual Accessibility</SectionHeading>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Insurance awareness should not depend on a person&apos;s ability to understand complex English-language policy
            documents. RedoClaim supports multilingual interaction and aims to make insurance information more accessible
            to people who are more comfortable communicating in Indian languages. We welcome review from language and
            insurance-domain experts to improve the accuracy and clarity of multilingual outputs.
          </p>
        </section>

        <section>
          <SectionHeading number="7">Who We Welcome Review From</SectionHeading>
          <CardGrid items={AUDIENCES} cols="md:grid-cols-2 lg:grid-cols-3" />
        </section>

        <section>
          <SectionHeading number="8">Possible Institutional Pilot</SectionHeading>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Where an institution considers RedoClaim appropriate, we would be happy to discuss a small, voluntary and
            measurable pilot designed together with the institution.
          </p>
        </section>

        <section>
          <SectionHeading number="9">Institutions Would Not Be Asked To</SectionHeading>
          <div className="mb-4"><BulletList items={NOT_ASKED} /></div>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            The proposed role is simply to make an independent free awareness resource available to people who choose to
            use it, subject to the institution&apos;s own policies and approval.
          </p>
        </section>

        <section>
          <SectionHeading number="10">Collaboration Principles</SectionHeading>
          <CardGrid items={PRINCIPLES} cols="md:grid-cols-2 lg:grid-cols-3" />
        </section>

        <section>
          <SectionHeading number="11">About The Student Behind RedoClaim</SectionHeading>
          <div className="card p-6" style={{ background: "var(--surface-1)" }}>
            <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Sarang Menon</h3>
            <p className="text-sm mb-4" style={{ color: "#A78BFA" }}>
              Class 10 Student · Developer · AI/ML & STEM Innovator
            </p>
            <p className="text-sm leading-relaxed mb-3" style={{ color: "var(--text-secondary)" }}>
              Sarang is a student developer from Keralam with a strong interest in using technology to address real-world
              challenges and create practical solutions with social value. His interests span AI, machine learning,
              software development, data and emerging technologies, with a particular focus on projects that can improve
              access to information, support communities and make complex problems easier to navigate.
            </p>
            <p className="text-sm leading-relaxed mb-3" style={{ color: "var(--text-secondary)" }}>
              RedoClaim reflects this approach. It explores how AI, document analysis and retrieval-based systems can help
              policyholders better understand complex insurance information and identify appropriate avenues for further
              assistance.
            </p>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Sarang is particularly interested in learning from domain experts and institutions and in developing
              technology that is not only technically useful, but also responsible, accessible and meaningful to the
              people it is designed to support.
            </p>
            {profileLinks.length > 0 && (
              <div className="flex gap-4 text-sm mt-5 flex-wrap">
                {profileLinks.map(([label, href]) => (
                  <a key={label} href={href} target="_blank" rel="noopener noreferrer" className="underline" style={{ color: "#A78BFA" }}>
                    {label}
                  </a>
                ))}
              </div>
            )}
          </div>
        </section>

        <section>
          <SectionHeading number="12">Interested In Reviewing Or Collaborating?</SectionHeading>
          <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--text-secondary)" }}>
            We would be grateful to hear from organisations or professionals who can help Sarang make RedoClaim more
            accurate, responsible and accessible.
          </p>
          <div className="flex gap-3 flex-wrap">
            {demoHref && <a href={demoHref} className="btn-primary text-sm px-5 py-2.5">Request A Demonstration</a>}
            {PROPOSAL_URL && (
              <a href={PROPOSAL_URL} target="_blank" rel="noopener noreferrer" className="btn-secondary text-sm px-5 py-2.5">
                Download One-Page Proposal
              </a>
            )}
            {guardianHref && <a href={guardianHref} className="btn-secondary text-sm px-5 py-2.5">Contact Parent/Guardian</a>}
          </div>
        </section>

        <section
          className="card p-6 space-y-3"
          style={{ background: "rgba(251,191,36,0.07)", borderColor: "rgba(251,191,36,0.25)" }}
        >
          <p className="text-sm leading-relaxed" style={{ color: "#FCD34D", opacity: 0.9 }}>
            RedoClaim is an independent, student-developed AI tool. It is not a government service, regulator, insurer,
            hospital, legal service or insurance company.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#FCD34D", opacity: 0.9 }}>
            Its output is intended to assist users in understanding documents and information and should not be treated
            as legal, financial or insurance advice.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#FCD34D", opacity: 0.9 }}>
            RedoClaim does not guarantee claim approval, claim reversal, settlement or compensation.
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#FCD34D", opacity: 0.9 }}>
            Users should independently verify important information and use the appropriate official grievance and
            escalation mechanisms.
          </p>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
