"use client";
import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp, Copy, Check } from "lucide-react";
import { useT } from "@/lib/i18n/useT";
import type { AssistantModule } from "@/types/assistant";

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold uppercase tracking-widest mb-1.5" style={{ color: "var(--text-tertiary)" }}>
        {title}
      </p>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Item({ title, sub, tag }: { title?: string | null; sub?: string | null; tag?: string | null }) {
  if (!title && !sub) return null;
  return (
    <div className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-4)" }}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{title}</p>
        {tag ? (
          <span className="text-[10px] uppercase tracking-wider shrink-0" style={{ color: "#C4B5FD" }}>{tag}</span>
        ) : null}
      </div>
      {sub ? <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{sub}</p> : null}
    </div>
  );
}

export default function ModuleCard({ module }: { module: AssistantModule }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const d = module.data || {};
  const failed = module.status !== "ok";

  const copyLetter = async () => {
    try {
      await navigator.clipboard.writeText(String(d.letter || ""));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-4)" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-semibold" style={{ color: failed ? "#FCD34D" : "var(--text-primary)" }}>
          {module.label}
        </span>
        {open ? <ChevronUp size={14} style={{ color: "var(--text-tertiary)" }} /> : <ChevronDown size={14} style={{ color: "var(--text-tertiary)" }} />}
      </button>

      {open && (
        <div className="px-4 pb-4 border-t" style={{ borderColor: "var(--surface-4)" }}>
          {failed && module.message ? (
            <p className="text-xs mt-3" style={{ color: "#FCD34D" }}>{module.message}</p>
          ) : null}

          {module.highlights.length > 0 && (
            <ul className="mt-3 space-y-1.5 pl-4 list-disc text-xs" style={{ color: "var(--text-secondary)" }}>
              {module.highlights.map((h, i) => (
                <li key={i}>{h}</li>
              ))}
            </ul>
          )}

          {Array.isArray(d.issues) && d.issues.length > 0 && (
            <Block title="Potential issues">
              {d.issues.map((x: any, i: number) => (
                <Item key={i} title={x.title} sub={[x.reference, x.argument].filter(Boolean).join(" - ")} tag={x.severity} />
              ))}
            </Block>
          )}
          {Array.isArray(d.escalation) && d.escalation.length > 0 && (
            <Block title="Where you can escalate">
              {d.escalation.map((x: any, i: number) => (
                <Item key={i} title={`${x.step}. ${x.route}`} sub={[x.how, x.cost ? `Cost: ${x.cost}` : null].filter(Boolean).join(" ")} />
              ))}
            </Block>
          )}
          {Array.isArray(d.deductions_reviewed) && d.deductions_reviewed.length > 0 && (
            <Block title="Deductions reviewed">
              {d.deductions_reviewed.map((x: any, i: number) => (
                <Item key={i} title={x.reason} sub={x.explanation} tag={x.justified === false ? "questionable" : x.justified ? "supported" : null} />
              ))}
            </Block>
          )}
          {Array.isArray(d.red_flags) && d.red_flags.length > 0 && (
            <Block title="Changes to review">
              {d.red_flags.map((x: any, i: number) => (
                <Item key={i} title={`${x.field}: ${x.old} to ${x.new}`} sub={x.explanation} tag={x.severity} />
              ))}
            </Block>
          )}
          {Array.isArray(d.precedents) && d.precedents.length > 0 && (
            <Block title="Similar cases">
              {d.precedents.map((x: any, i: number) => (
                <Item key={i} title={`${x.case_name} (${x.court})`} sub={x.how_to_use || x.summary} />
              ))}
            </Block>
          )}
          {Array.isArray(d.waiting_periods) && d.waiting_periods.length > 0 && (
            <Block title="Waiting periods">
              {d.waiting_periods.map((x: any, i: number) => (
                <Item key={i} title={`${x.condition} (${x.duration})`} sub={x.note} tag={x.status ? String(x.status).replace(/_/g, " ") : x.risk_level} />
              ))}
            </Block>
          )}
          {Array.isArray(d.exclusions) && d.exclusions.length > 0 && (
            <Block title="Exclusions">
              {d.exclusions.map((x: any, i: number) => (
                <Item key={i} title={x.title} sub={x.description} tag={x.risk_level} />
              ))}
            </Block>
          )}
          {Array.isArray(d.rows) && d.rows.length > 0 && (
            <Block title={Array.isArray(d.policies) ? d.policies.join(" | ") : "Comparison"}>
              {d.rows.map((x: any, i: number) => (
                <Item key={i} title={x.attribute} sub={(x.values || []).join(" | ")} />
              ))}
            </Block>
          )}
          {Array.isArray(d.steps) && d.steps.length > 0 && (
            <Block title="Steps">
              {d.steps.map((x: any, i: number) => (
                <Item key={i} title={`${x.step}. ${x.action}`} sub={x.detail} />
              ))}
            </Block>
          )}
          {Array.isArray(d.how_to_port) && d.how_to_port.length > 0 && (
            <Block title="How to port">
              {d.how_to_port.map((x: string, i: number) => (
                <Item key={i} title={x} />
              ))}
            </Block>
          )}

          {d.letter ? (
            <div className="mt-3">
              <div className="flex justify-end mb-1.5">
                <button onClick={copyLetter} className="flex items-center gap-1.5 text-xs" style={{ color: "#A78BFA" }}>
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  {copied ? t("as_copied") : t("as_copy")}
                </button>
              </div>
              <pre
                className="text-xs whitespace-pre-wrap rounded-lg p-3 max-h-96 overflow-y-auto"
                style={{ background: "var(--surface-2)", border: "1px solid var(--surface-4)", color: "var(--text-primary)", fontFamily: "inherit" }}
              >
                {String(d.letter)}
              </pre>
            </div>
          ) : null}

          {module.links.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {module.links.map((l) => (
                <Link key={l.href} href={l.href} className="btn-primary text-xs px-3 py-2">
                  {l.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
