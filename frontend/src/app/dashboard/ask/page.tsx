"use client";
import { useEffect, useState, useRef } from "react";
import { analysisApi, claimsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Send, Loader2, Sparkles, Bot, User as UserIcon } from "lucide-react";
import { useT } from "@/lib/i18n/useT";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Claim } from "@/types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function AskAIPage() {
  const t = useT();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [claimId, setClaimId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    claimsApi.list().then((res) => setClaims(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const ask = async () => {
    const q = question.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setLoading(true);
    try {
      const res = await analysisApi.ask(q, claimId || undefined);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.answer }]);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Something went wrong asking the assistant");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{ color: "var(--text-primary)" }}>
      <div>
        <h2 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          {t("nav_ask_ai")}
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          {t("ask_subtitle")}
        </p>
      </div>

      <DisclaimerBanner variant="inline" context="general" />

      {claims.length > 0 && (
        <div className="flex items-center gap-2">
          <label className="text-xs shrink-0" style={{ color: "var(--text-tertiary)" }}>
            {t("ask_link_claim")}
          </label>
          <select
            value={claimId}
            onChange={(e) => setClaimId(e.target.value)}
            className="text-sm rounded-lg px-3 py-1.5 flex-1"
            style={{
              background: "var(--surface-2)",
              border: "1px solid var(--surface-5)",
              color: "var(--text-primary)",
            }}
          >
            <option value="">None</option>
            {claims.map((c) => (
              <option key={c.id} value={c.id}>
                {c.insurer_name} — {c.policy_number || c.id.slice(0, 8)}
              </option>
            ))}
          </select>
        </div>
      )}

      <div
        className="rounded-2xl flex flex-col"
        style={{ background: "var(--surface-1)", border: "1px solid var(--surface-4)", minHeight: "420px" }}
      >
        <div className="flex-1 p-4 space-y-4 overflow-y-auto" style={{ maxHeight: "55vh" }}>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center py-16 gap-2">
              <Sparkles size={22} style={{ color: "var(--text-tertiary)" }} />
              <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                {t("ask_empty_hint")}
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex gap-2.5 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                  style={{ background: "rgba(139,92,246,0.2)" }}
                >
                  <Bot size={13} style={{ color: "#A78BFA" }} />
                </div>
              )}
              <div
                className="rounded-xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap max-w-[80%]"
                style={
                  m.role === "user"
                    ? { background: "rgba(139,92,246,0.15)", color: "var(--text-primary)" }
                    : { background: "var(--surface-2)", color: "var(--text-primary)" }
                }
              >
                {m.content}
              </div>
              {m.role === "user" && (
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                  style={{ background: "var(--surface-3)" }}
                >
                  <UserIcon size={13} style={{ color: "var(--text-secondary)" }} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-2.5 justify-start">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                style={{ background: "rgba(139,92,246,0.2)" }}
              >
                <Bot size={13} style={{ color: "#A78BFA" }} />
              </div>
              <div
                className="rounded-xl px-3.5 py-2.5 text-sm flex items-center gap-2"
                style={{ background: "var(--surface-2)", color: "var(--text-tertiary)" }}
              >
                <Loader2 size={13} className="animate-spin" /> {t("ask_thinking")}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-3 border-t flex items-end gap-2" style={{ borderColor: "var(--surface-4)" }}>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("ask_input_placeholder")}
            rows={1}
            className="flex-1 text-sm rounded-lg px-3 py-2 resize-none"
            style={{
              background: "var(--surface-2)",
              border: "1px solid var(--surface-5)",
              color: "var(--text-primary)",
            }}
          />
          <button
            onClick={ask}
            disabled={loading || !question.trim()}
            className="btn-primary text-xs px-3 py-2.5 flex items-center gap-1.5 disabled:opacity-50"
          >
            <Send size={13} /> {t("ask_send")}
          </button>
        </div>
      </div>
    </div>
  );
}
