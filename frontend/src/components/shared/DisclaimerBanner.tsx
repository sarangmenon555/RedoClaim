"use client";
import { useState } from "react";
import { AlertTriangle, X, ChevronDown, ChevronUp } from "lucide-react";
import { useT } from "@/lib/i18n/useT";

interface Props {
  variant?: "banner" | "inline" | "footer";
  context?: "general" | "audit" | "appeal" | "cis" | "portability" | "timeline";
  className?: string;
}

const CONTEXT_KEYS: Record<string, string> = {
  general: "disc_ctx_general",
  audit: "disc_ctx_audit",
  appeal: "disc_ctx_appeal",
  cis: "disc_ctx_cis",
  portability: "disc_ctx_portability",
  timeline: "disc_ctx_timeline",
};

export function DisclaimerBanner({ variant = "banner", context = "general", className = "" }: Props) {
  const [dismissed, setDismissed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const t = useT();
  const message = t(CONTEXT_KEYS[context]);

  if (variant === "footer") {
    return (
      <div className={`text-xs leading-relaxed ${className}`} style={{color:"var(--text-tertiary)"}}>
        <span style={{color:"#FCD34D"}}>⚠️ {t("disc_ai_tool_label")}</span>{" "}
        {message}{" "}
        <a href="https://irdai.gov.in/home" target="_blank" rel="noopener noreferrer"
          className="underline" style={{color:"#A78BFA"}}>{t("disc_verify_irdai")}</a>
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div className={`flex items-start gap-2 p-3 rounded-xl ${className}`}
        style={{background:"rgba(251,191,36,0.07)",border:"1px solid rgba(251,191,36,0.15)"}}>
        <AlertTriangle size={13} style={{color:"#FBBF24"}} className="mt-0.5 shrink-0" />
        <p className="text-xs leading-relaxed" style={{color:"#FCD34D"}}>
          <strong>{t("disc_verify_before_use")}</strong> {message}
        </p>
      </div>
    );
  }

  if (dismissed) return null;

  return (
    <div className={`rounded-xl overflow-hidden ${className}`}
      style={{background:"rgba(251,191,36,0.06)",border:"1px solid rgba(251,191,36,0.15)"}}>
      <div className="p-4 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <AlertTriangle size={15} style={{color:"#FBBF24"}} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold" style={{color:"#FCD34D"}}>{t("disc_not_legal_advice_title")}</p>
            <p className="text-xs mt-0.5 leading-relaxed" style={{color:"rgba(252,211,77,0.8)"}}>
              {message}
            </p>
            <button onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs font-medium mt-1.5 transition"
              style={{color:"rgba(252,211,77,0.7)"}}>
              {expanded ? t("disc_show_less") : t("disc_full_disclaimer")}
              {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
            </button>
            {expanded && (
              <div className="mt-3 pt-3 space-y-2 text-xs leading-relaxed"
                style={{borderTop:"1px solid rgba(251,191,36,0.15)",color:"rgba(252,211,77,0.7)"}}>
                <p><strong style={{color:"#FCD34D"}}>RedoClaim is an AI research tool</strong>, not a law firm. AI models can hallucinate, misread documents, and cite regulations inaccurately.</p>
                <p><strong style={{color:"#FCD34D"}}>Before sending any letter:</strong> verify every IRDAI citation at{" "}
                  <a href="https://irdai.gov.in/home" target="_blank" rel="noopener noreferrer"
                    className="underline" style={{color:"#A78BFA"}}>irdai.gov.in</a> and correct all factual errors.</p>
                <p><strong style={{color:"#FCD34D"}}>For complex cases:</strong> consult a licensed insurance advocate or contact{" "}
                  <a href="https://nalsa.gov.in" target="_blank" rel="noopener noreferrer"
                    className="underline" style={{color:"#A78BFA"}}>NALSA</a> for free legal aid.</p>
              </div>
            )}
          </div>
        </div>
        <button onClick={() => setDismissed(true)} style={{color:"rgba(251,191,36,0.5)"}}
          className="transition hover:opacity-100 shrink-0 mt-0.5">
          <X size={14} />
        </button>
      </div>
    </div>
  );
}

export function AIOutputLabel({ className = "" }: { className?: string }) {
  const t = useT();
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${className}`}
      style={{background:"rgba(251,191,36,0.1)",color:"#FCD34D",border:"1px solid rgba(251,191,36,0.2)"}}>
      <AlertTriangle size={9} /> {t("disc_ai_generated")}
    </span>
  );
}

export function LetterDisclaimer() {
  return (
    <div className="p-4"
      style={{background:"rgba(251,191,36,0.06)",borderTop:"1px solid rgba(251,191,36,0.12)"}}>
      <div className="flex items-start gap-2">
        <AlertTriangle size={13} style={{color:"#FBBF24"}} className="mt-0.5 shrink-0" />
        <div className="text-xs leading-relaxed space-y-1" style={{color:"rgba(252,211,77,0.8)"}}>
          <p><strong style={{color:"#FCD34D"}}>Before sending:</strong> Read every line. Verify your name, policy number, dates, and amounts are correct. Check all IRDAI citations at{" "}
            <a href="https://www.irdai.gov.in" target="_blank" rel="noopener noreferrer"
              className="underline" style={{color:"#A78BFA"}}>irdai.gov.in</a>.
          </p>
          <p><strong style={{color:"#FCD34D"}}>Not legal advice.</strong> For claims above ₹10 Lakhs, consult a licensed advocate or contact{" "}
            <a href="https://nalsa.gov.in" target="_blank" rel="noopener noreferrer"
              className="underline" style={{color:"#A78BFA"}}>NALSA</a> for free legal aid.
          </p>
        </div>
      </div>
    </div>
  );
}
