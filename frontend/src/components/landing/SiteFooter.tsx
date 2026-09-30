import { ShieldCheck } from "lucide-react";

const LINKS: [string, string][] = [
  ["IRDAI", "https://irdai.gov.in/home"],
  ["Bima Bharosa", "https://bimabharosa.irdai.gov.in/"],
  ["e-Jagriti", "https://e-jagriti.gov.in/"],
  ["Institutional Review", "/institutional-review"],
  ["Disclaimer", "/disclaimer"],
];

export default function SiteFooter() {
  return (
    <footer className="border-t py-8" style={{ borderColor: "var(--surface-4)", background: "var(--surface-1)" }}>
      <div className="max-w-6xl mx-auto px-4 space-y-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded-md flex items-center justify-center"
              style={{ background: "linear-gradient(135deg,#7C3AED,#4F46E5)" }}
            >
              <ShieldCheck size={12} className="text-white" />
            </div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>RedoClaim</span>
            <span style={{ color: "var(--text-tertiary)" }}>— AI Powered Insurance Claim Analysis Tool</span>
          </div>
          <div className="flex gap-4 flex-wrap justify-center text-xs" style={{ color: "var(--text-tertiary)" }}>
            {LINKS.map(([label, href]) => (
              <a
                key={label}
                href={href}
                target={href.startsWith("http") ? "_blank" : undefined}
                rel="noopener noreferrer"
                className="hover:text-violet-400 transition-colors"
              >
                {label}
              </a>
            ))}
          </div>
        </div>
        <p className="text-xs text-center md:text-left leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
          RedoClaim is independently developed and is not affiliated with or endorsed by IRDAI, any insurer, the
          Insurance Ombudsman or any government institution unless explicitly stated.
        </p>
      </div>
    </footer>
  );
}
