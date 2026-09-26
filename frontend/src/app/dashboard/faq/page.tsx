"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { BookOpen, ChevronDown, ChevronRight, Search } from "lucide-react";
import { FAQ_ENTRIES } from "@/lib/faq-data";

export default function FaqPage() {
  const [query, setQuery] = useState("");
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FAQ_ENTRIES;
    return FAQ_ENTRIES.filter(
      (e) => e.question.toLowerCase().includes(q) || e.category.toLowerCase().includes(q) || e.answer.toLowerCase().includes(q)
    );
  }, [query]);

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <BookOpen size={22} style={{ color: "#A78BFA" }} /> Common Rejection Reasons
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          A quick-reference library of the most common insurance rejection reasons in India, and what
          you can actually do about each one.
        </p>
      </div>

      <div className="relative">
        <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
        <input
          className="input pl-10"
          placeholder="Search rejection reasons..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          suppressHydrationWarning
        />
      </div>

      <div className="space-y-3">
        {filtered.length === 0 && (
          <p className="text-sm text-center py-10" style={{ color: "var(--text-tertiary)" }}>
            No matches. Try a different search term, or ask the AI directly.
          </p>
        )}

        {filtered.map((entry, i) => {
          const isOpen = openIndex === i;
          return (
            <div key={i} className="card overflow-hidden" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
              <button
                onClick={() => setOpenIndex(isOpen ? null : i)}
                className="w-full flex items-start justify-between gap-3 p-4 text-left"
                suppressHydrationWarning>
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#A78BFA" }}>{entry.category}</span>
                  <p className="text-sm font-medium mt-1" style={{ color: "var(--text-primary)" }}>{entry.question}</p>
                </div>
                {isOpen ? <ChevronDown size={16} className="shrink-0 mt-1" style={{ color: "var(--text-tertiary)" }} />
                         : <ChevronRight size={16} className="shrink-0 mt-1" style={{ color: "var(--text-tertiary)" }} />}
              </button>
              {isOpen && (
                <div className="px-4 pb-4 space-y-3">
                  <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{entry.answer}</p>
                  {entry.relatedTool && (
                    <Link href={entry.relatedTool.href} className="inline-block text-xs font-semibold px-3 py-1.5 rounded-full transition"
                      style={{ background: "rgba(139,92,246,0.12)", color: "#A78BFA", border: "1px solid rgba(139,92,246,0.25)" }}>
                      {entry.relatedTool.label} →
                    </Link>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="card p-5 text-center" style={{ background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.15)" }}>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Don't see your situation here?</p>
        <Link href="/dashboard/ask" className="btn-primary inline-flex mt-3 px-4 py-2 text-sm">Ask AI about your specific case</Link>
      </div>
    </div>
  );
}
