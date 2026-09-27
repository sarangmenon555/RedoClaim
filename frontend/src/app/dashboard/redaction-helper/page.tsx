"use client";
import { useMemo, useState } from "react";
import { EyeOff, ShieldCheck, AlertTriangle } from "lucide-react";

interface Finding {
  type: string;
  match: string;
  index: number;
}

// Pure regex, runs entirely in the browser — nothing here is ever sent to
// any server. Aadhaar/PAN/account-number patterns are approximate (format
// checks, not validity checks) — this flags LIKELY sensitive fields for the
// user to review, it doesn't guarantee detection of every possible format.
const PATTERNS: { type: string; regex: RegExp }[] = [
  { type: "Aadhaar number", regex: /\b\d{4}\s?\d{4}\s?\d{4}\b/g },
  { type: "PAN number", regex: /\b[A-Z]{5}\d{4}[A-Z]\b/g },
  { type: "Bank account number", regex: /\b\d{9,18}\b/g },
  { type: "IFSC code", regex: /\b[A-Z]{4}0[A-Z0-9]{6}\b/g },
  { type: "Phone number", regex: /\b(?:\+91[\s-]?)?[6-9]\d{9}\b/g },
  { type: "Email address", regex: /\b[\w.+-]+@[\w-]+\.[A-Za-z]{2,}\b/g },
  { type: "Credit/Debit card number", regex: /\b(?:\d[ -]?){13,16}\b/g },
];

function findSensitiveData(text: string): Finding[] {
  const findings: Finding[] = [];
  for (const { type, regex } of PATTERNS) {
    let match;
    const re = new RegExp(regex);
    while ((match = re.exec(text)) !== null) {
      findings.push({ type, match: match[0], index: match.index });
      if (match.index === re.lastIndex) re.lastIndex++; // avoid infinite loop on zero-width matches
    }
  }
  return findings.sort((a, b) => a.index - b.index);
}

function redactText(text: string, findings: Finding[]): string {
  let result = text;
  // Redact from the end so earlier indices stay valid
  const sorted = [...findings].sort((a, b) => b.index - a.index);
  for (const f of sorted) {
    result = result.slice(0, f.index) + "█".repeat(f.match.length) + result.slice(f.index + f.match.length);
  }
  return result;
}

export default function RedactionHelperPage() {
  const [input, setInput] = useState("");
  const [showRedacted, setShowRedacted] = useState(false);

  const findings = useMemo(() => (input.trim() ? findSensitiveData(input) : []), [input]);
  const redacted = useMemo(() => redactText(input, findings), [input, findings]);

  const copyRedacted = () => {
    navigator.clipboard.writeText(redacted);
  };

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <EyeOff size={22} style={{ color: "#A78BFA" }} /> Document Redaction Helper
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Before sharing a document with a lawyer, a forum, or pasting it anywhere — check what looks like
          sensitive personal data first. This runs entirely in your browser; nothing here is sent anywhere.
        </p>
      </div>

      <div className="rounded-xl p-4 flex items-start gap-2.5" style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)" }}>
        <ShieldCheck size={15} className="mt-0.5 shrink-0" style={{ color: "#4ADE80" }} />
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          100% client-side — the text you paste here never leaves your browser or touches our servers.
        </p>
      </div>

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <textarea
          className="input min-h-[180px] font-mono text-xs"
          placeholder="Paste document text here to check for Aadhaar numbers, PAN, bank details, phone numbers, etc."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          suppressHydrationWarning
        />
      </div>

      {input.trim() && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          {findings.length === 0 ? (
            <div className="flex items-center gap-2 text-sm" style={{ color: "#4ADE80" }}>
              <ShieldCheck size={16} /> No obvious sensitive patterns detected.
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: "#F87171" }}>
                <AlertTriangle size={16} /> {findings.length} potentially sensitive item(s) found
              </div>
              <div className="space-y-1.5">
                {findings.map((f, i) => (
                  <div key={i} className="flex justify-between text-xs rounded-lg px-3 py-2" style={{ background: "var(--surface-2)" }}>
                    <span style={{ color: "var(--text-tertiary)" }}>{f.type}</span>
                    <span className="font-mono" style={{ color: "var(--text-primary)" }}>{f.match}</span>
                  </div>
                ))}
              </div>

              <button onClick={() => setShowRedacted(!showRedacted)} className="btn-secondary text-xs px-3 py-1.5" suppressHydrationWarning>
                {showRedacted ? "Hide" : "Show"} redacted version
              </button>

              {showRedacted && (
                <div className="space-y-2">
                  <pre className="whitespace-pre-wrap text-xs font-mono p-3 rounded-lg" style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}>
                    {redacted}
                  </pre>
                  <button onClick={copyRedacted} className="btn-primary text-xs px-3 py-1.5" suppressHydrationWarning>
                    Copy redacted text
                  </button>
                </div>
              )}
            </>
          )}
          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            Pattern-matching only — this flags LIKELY sensitive fields for your review, it doesn't guarantee
            every possible format is caught. Always do a final manual check before sharing.
          </p>
        </div>
      )}
    </div>
  );
}
