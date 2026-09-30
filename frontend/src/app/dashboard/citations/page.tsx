"use client";
import { useMemo, useState } from "react";
import { Scale, Search } from "lucide-react";
import { CITATIONS } from "@/lib/citation-data";

export default function CitationsPage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return CITATIONS;
    return CITATIONS.filter(
      (c) => c.law.toLowerCase().includes(q) || c.title.toLowerCase().includes(q) ||
             c.section.toLowerCase().includes(q) || c.summary.toLowerCase().includes(q)
    );
  }, [query]);

  const grouped = filtered.reduce<Record<string, typeof CITATIONS>>((acc, c) => {
    (acc[c.law] ||= []).push(c);
    return acc;
  }, {});

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Scale size={22} style={{ color: "#A78BFA" }} /> Regulatory Citation Library
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          The actual IRDAI circulars, Consumer Protection Act, 2019 sections, and Ombudsman Rules our audit
          tool cites — read the source law directly instead of just trusting the AI's citation.
        </p>
      </div>

      <div className="relative">
        <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
        <input
          className="input pl-10"
          placeholder="Search by law, section, or topic..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          suppressHydrationWarning
        />
      </div>

      <div className="space-y-6">
        {Object.entries(grouped).length === 0 && (
          <p className="text-sm text-center py-10" style={{ color: "var(--text-tertiary)" }}>No matches. Try a different search term.</p>
        )}
        {Object.entries(grouped).map(([law, citations]) => (
          <div key={law}>
            <h3 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "#A78BFA" }}>{law}</h3>
            <div className="space-y-2">
              {citations.map((c, i) => (
                <div key={i} className="card p-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
                  <p className="text-xs font-mono" style={{ color: "var(--text-tertiary)" }}>{c.section}</p>
                  <p className="text-sm font-semibold mt-1" style={{ color: "var(--text-primary)" }}>{c.title}</p>
                  <p className="text-sm mt-1.5 leading-relaxed" style={{ color: "var(--text-secondary)" }}>{c.summary}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-center" style={{ color: "var(--text-tertiary)" }}>
        Summarized for readability — always verify exact wording against the official IRDAI/government source before citing in a formal filing.
      </p>
    </div>
  );
}
