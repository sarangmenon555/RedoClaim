"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Paperclip, Mic, Send, Loader2, X, AlertCircle, Plus } from "lucide-react";
import toast from "react-hot-toast";
import { assistantApi, claimsApi, documentsApi } from "@/lib/api";
import { pollDocument } from "@/lib/poll";
import { useAuthStore } from "@/store/auth";
import { useLanguageStore } from "@/store/language";
import { useAssistantStore } from "@/store/assistant";
import { useT } from "@/lib/i18n/useT";
import MessageView from "@/components/assistant/MessageView";
import type { ChatMessage } from "@/types/assistant";
import type { Claim } from "@/types";

const MAX_FILES = 6;
const MAX_FILE_MB = 20;
const ACCEPTED = ".pdf,.jpg,.jpeg,.png,.webp,.tif,.tiff";
const SPEECH_LANG: Record<string, string> = {
  en: "en-IN", hi: "hi-IN", ml: "ml-IN", ta: "ta-IN", te: "te-IN", kn: "kn-IN",
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const newId = () => Math.random().toString(36).slice(2);

function waitForDocument(id: string): Promise<void> {
  return new Promise((resolve, reject) => {
    pollDocument(id, {
      onDone: () => resolve(),
      onFailed: () => reject(new Error("read_failed")),
      onTimeout: () => reject(new Error("timeout")),
      onAuthError: () => reject(new Error("auth")),
    });
  });
}

export default function DashboardPage() {
  const t = useT();
  const { user } = useAuthStore();
  const language = useLanguageStore((s) => s.language);
  const { messages, busy, addMessage, addDocuments, setContext, setBusy, reset } = useAssistantStore();

  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [stage, setStage] = useState<"idle" | "reading" | "thinking">("idle");
  const [listening, setListening] = useState(false);
  const [canSpeak, setCanSpeak] = useState(false);
  const [urgent, setUrgent] = useState<Claim[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const recognition = useRef<any>(null);

  useEffect(() => {
    const w = window as any;
    setCanSpeak(Boolean(w.SpeechRecognition || w.webkitSpeechRecognition));
    claimsApi
      .list()
      .then((r) => {
        const soon = (r.data as Claim[]).filter((c) => {
          if (!c.gro_deadline) return false;
          return Math.ceil((new Date(c.gro_deadline).getTime() - Date.now()) / 86400000) <= 5;
        });
        setUrgent(soon);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, busy]);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const incoming = Array.from(list);
    const tooBig = incoming.find((f) => f.size > MAX_FILE_MB * 1024 * 1024);
    if (tooBig) {
      toast.error(`${tooBig.name} is larger than ${MAX_FILE_MB} MB`);
      return;
    }
    setFiles((prev) => [...prev, ...incoming].slice(0, MAX_FILES));
    if (fileInput.current) fileInput.current.value = "";
  };

  const toggleMic = () => {
    const w = window as any;
    const Recognition = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!Recognition) return;
    if (listening && recognition.current) {
      recognition.current.stop();
      return;
    }
    const rec = new Recognition();
    rec.lang = SPEECH_LANG[language] || "en-IN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (event: any) => {
      const spoken = Array.from(event.results).map((r: any) => r[0].transcript).join(" ");
      setText((prev) => (prev ? `${prev} ${spoken}` : spoken));
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recognition.current = rec;
    setListening(true);
    rec.start();
  };

  const send = async (override?: string) => {
    const state = useAssistantStore.getState();
    if (state.busy) return;
    const message = (override ?? text).trim();
    const attached = override ? [] : files;
    if (!message && attached.length === 0) return;

    const history = state.messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
    const userMessage: ChatMessage = {
      id: newId(),
      role: "user",
      content: message,
      files: attached.map((f) => ({ name: f.name })),
    };
    addMessage(userMessage);
    if (!override) {
      setText("");
      setFiles([]);
    }
    setBusy(true);

    try {
      const newIds: string[] = [];
      if (attached.length > 0) {
        setStage("reading");
        for (const file of attached) {
          const res = await documentsApi.uploadAuto(file);
          const id = res.data.document_id as string;
          await waitForDocument(id);
          newIds.push(id);
        }
        addDocuments(newIds);
      }

      setStage("thinking");
      const current = useAssistantStore.getState();
      let reply = null;
      for (let attempt = 0; attempt < 4; attempt++) {
        try {
          const res = await assistantApi.ask({
            message,
            document_ids: current.documentIds,
            new_document_ids: newIds,
            context: current.context,
            history,
          });
          reply = res.data;
          break;
        } catch (e: any) {
          if (e?.response?.status === 409 && attempt < 3) {
            await sleep(3000);
            continue;
          }
          throw e;
        }
      }
      if (reply) {
        setContext(reply.context);
        addMessage({ id: newId(), role: "assistant", content: reply.answer, reply });
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const fallback =
        e?.message === "read_failed"
          ? "I could not read one of your documents. Please try a clearer photo or a PDF."
          : e?.message === "timeout"
          ? "Reading your document is taking longer than expected. Please try again in a moment."
          : "Something went wrong. Please try again.";
      addMessage({
        id: newId(),
        role: "assistant",
        content: typeof detail === "string" ? detail : fallback,
        error: true,
      });
    } finally {
      setBusy(false);
      setStage("idle");
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const composer = (
    <div
      className="rounded-2xl w-full"
      style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        addFiles(e.dataTransfer.files);
      }}
    >
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pt-3">
          {files.map((f, i) => (
            <span
              key={`${f.name}-${i}`}
              className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md"
              style={{ background: "var(--surface-2)", color: "var(--text-secondary)", border: "1px solid var(--surface-4)" }}
            >
              {f.name}
              <button
                aria-label={t("as_remove")}
                title={t("as_remove")}
                onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
              >
                <X size={11} />
              </button>
            </span>
          ))}
        </div>
      )}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        rows={3}
        placeholder={t("as_placeholder")}
        className="w-full bg-transparent resize-none px-4 py-3 text-sm outline-none"
        style={{ color: "var(--text-primary)" }}
      />
      <div className="flex items-center justify-between px-3 py-2.5 border-t" style={{ borderColor: "var(--surface-4)" }}>
        <div className="flex items-center gap-1">
          <input
            ref={fileInput}
            type="file"
            multiple
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
          <button
            onClick={() => fileInput.current?.click()}
            aria-label={t("as_attach")}
            title={t("as_attach")}
            className="w-9 h-9 flex items-center justify-center rounded-lg transition"
            style={{ color: "var(--text-secondary)" }}
          >
            <Paperclip size={16} />
          </button>
          {canSpeak && (
            <button
              onClick={toggleMic}
              aria-label={t("as_mic")}
              title={t("as_mic")}
              className="w-9 h-9 flex items-center justify-center rounded-lg transition"
              style={{
                color: listening ? "#F87171" : "var(--text-secondary)",
                background: listening ? "rgba(248,113,113,0.12)" : "transparent",
              }}
            >
              <Mic size={16} />
            </button>
          )}
        </div>
        <button
          onClick={() => send()}
          disabled={busy || (!text.trim() && files.length === 0)}
          className="btn-primary text-sm px-4 py-2 flex items-center gap-2 disabled:opacity-50"
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {t("as_send")}
        </button>
      </div>
    </div>
  );

  const urgentBanner = urgent.length > 0 && (
    <div
      className="rounded-xl p-3 flex items-start gap-3 w-full"
      style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}
    >
      <AlertCircle size={16} style={{ color: "#F87171" }} className="shrink-0 mt-0.5" />
      <div className="text-xs" style={{ color: "#FCA5A5" }}>
        <p className="font-semibold">{t("db_urgent_title")}</p>
        {urgent.map((c) => (
          <p key={c.id} className="mt-0.5">{t("db_gro_vs")} {c.insurer_name}</p>
        ))}
        <Link href="/dashboard/timeline" className="underline inline-block mt-1">{t("db_view_timeline")}</Link>
      </div>
    </div>
  );

  if (messages.length === 0) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex flex-col items-center justify-center gap-6 max-w-3xl mx-auto animate-fade-in">
        {urgentBanner}
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-light tracking-tight" style={{ color: "var(--text-primary)" }}>
            {user?.full_name ? `${user.full_name.split(" ")[0]}, ` : ""}
            {t("as_title")}
          </h2>
          <p className="text-sm max-w-xl mx-auto" style={{ color: "var(--text-secondary)" }}>{t("as_sub")}</p>
        </div>
        {composer}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col min-h-[calc(100vh-8rem)] animate-fade-in">
      <div className="flex-1 space-y-6 pb-6">
        <div className="flex justify-end">
          <button
            onClick={reset}
            disabled={busy}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg disabled:opacity-50"
            style={{ color: "#C4B5FD", border: "1px solid rgba(139,92,246,0.25)", background: "rgba(139,92,246,0.08)" }}
          >
            <Plus size={12} />
            {t("as_new_chat")}
          </button>
        </div>
        {urgentBanner}
        {messages.map((m) => (
          <MessageView key={m.id} message={m} onSuggest={(s) => send(s)} disabled={busy} />
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
            <Loader2 size={14} className="animate-spin" />
            {stage === "reading" ? t("as_reading") : t("as_thinking")}
          </div>
        )}
        <div ref={bottom} />
      </div>
      <div className="sticky bottom-4">{composer}</div>
    </div>
  );
}
