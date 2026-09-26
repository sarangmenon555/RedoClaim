"use client";
import { useState } from "react";
import { analysisApi } from "@/lib/api";
import { useLanguageStore } from "@/store/language";
import toast from "react-hot-toast";
import { HelpCircle, Loader2, Lightbulb } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";

interface Explanation {
  term: string;
  plain_explanation: string;
  example: string;
  why_it_matters: string;
}

const SAMPLE_TERMS = [
  "Moratorium period",
  "Sub-limit on room rent",
  "Co-payment clause",
  "Pre-existing disease waiting period",
  "Deficiency in service",
];

export default function ExplainTermPage() {
  const language = useLanguageStore((s) => s.language);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Explanation | null>(null);

  const runExplain = async (text?: string) => {
    const term = (text ?? input).trim();
    if (!term) {
      toast.error("Paste a term or clause first.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await analysisApi.explainTerm(term, language);
      setResult(res.data);
    } catch {
      toast.error("Couldn't explain that. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <HelpCircle size={22} style={{ color: "#A78BFA" }} /> Explain a Term
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Paste any insurance term or policy clause and get a plain-language explanation — no jargon.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <textarea
          className="input min-h-[100px]"
          placeholder="e.g. 'Room rent shall be limited to 1% of sum insured per day' or just 'moratorium period'"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          suppressHydrationWarning
        />

        <div className="flex flex-wrap gap-2">
          {SAMPLE_TERMS.map((term) => (
            <button
              key={term}
              onClick={() => { setInput(term); runExplain(term); }}
              className="text-xs px-3 py-1.5 rounded-full transition"
              style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)", color: "var(--text-secondary)" }}
              suppressHydrationWarning>
              {term}
            </button>
          ))}
        </div>

        <button onClick={() => runExplain()} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Explaining...</> : "Explain this"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{result.term}</h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{result.plain_explanation}</p>

          {result.example && (
            <div className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
              <p className="text-xs font-semibold mb-1" style={{ color: "#A78BFA" }}>Example</p>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.example}</p>
            </div>
          )}

          {result.why_it_matters && (
            <div className="flex items-start gap-2">
              <Lightbulb size={14} className="mt-0.5 shrink-0" style={{ color: "#FBBF24" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.why_it_matters}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
