"use client";
import { FileText, Paperclip } from "lucide-react";
import { useT } from "@/lib/i18n/useT";
import type { ChatMessage } from "@/types/assistant";
import FormattedText from "./FormattedText";
import ModuleCard from "./ModuleCard";

interface Props {
  message: ChatMessage;
  onSuggest: (text: string) => void;
  disabled: boolean;
}

export default function MessageView({ message, onSuggest, disabled }: Props) {
  const t = useT();

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[85%] rounded-2xl px-4 py-3 space-y-2"
          style={{ background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.25)" }}
        >
          {message.files && message.files.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {message.files.map((f, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-md"
                  style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}
                >
                  <Paperclip size={11} />
                  {f.name}
                </span>
              ))}
            </div>
          )}
          {message.content ? (
            <p className="text-sm whitespace-pre-wrap" style={{ color: "var(--text-primary)" }}>{message.content}</p>
          ) : null}
        </div>
      </div>
    );
  }

  const reply = message.reply;
  return (
    <div className="space-y-3">
      <div className="rounded-2xl px-5 py-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-4)" }}>
        {message.error ? (
          <p className="text-sm" style={{ color: "#FCA5A5" }}>{message.content}</p>
        ) : (
          <FormattedText text={message.content} />
        )}
      </div>

      {reply && reply.documents.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {reply.documents.map((d) => (
            <span
              key={d.id}
              className="inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-md"
              style={{ background: "var(--surface-2)", color: "var(--text-tertiary)", border: "1px solid var(--surface-4)" }}
            >
              <FileText size={11} />
              {d.label}
            </span>
          ))}
        </div>
      )}

      {reply && reply.needs.length > 0 && (
        <div className="rounded-xl p-4" style={{ background: "rgba(251,191,36,0.07)", border: "1px solid rgba(251,191,36,0.2)" }}>
          <p className="text-xs font-semibold mb-2" style={{ color: "#FCD34D" }}>{t("as_need_more")}</p>
          <ul className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
            {reply.needs.flatMap((n) =>
              n.fields.map((f) => (
                <li key={`${n.intent}-${f.key}`}>
                  {f.label}
                  {f.hint ? <span style={{ color: "var(--text-tertiary)" }}> ({f.hint})</span> : null}
                </li>
              ))
            )}
          </ul>
        </div>
      )}

      {reply && reply.modules.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--text-tertiary)" }}>
            {t("as_details")}
          </p>
          {reply.modules.map((m) => (
            <ModuleCard key={m.id} module={m} />
          ))}
        </div>
      )}

      {reply && reply.suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {reply.suggestions.map((s) => (
            <button
              key={s.id}
              disabled={disabled}
              onClick={() => onSuggest(s.message)}
              className="text-xs px-3 py-1.5 rounded-full transition disabled:opacity-50"
              style={{ border: "1px solid rgba(139,92,246,0.3)", color: "#C4B5FD", background: "rgba(139,92,246,0.08)" }}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {reply?.ai_disclaimer ? (
        <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-tertiary)" }}>{reply.ai_disclaimer}</p>
      ) : null}
    </div>
  );
}
