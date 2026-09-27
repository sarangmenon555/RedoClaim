"use client";
import { useState } from "react";
import { MapPin, Mail, Search } from "lucide-react";
import { OMBUDSMAN_OFFICES, CITY_TO_CENTER } from "@/lib/ombudsman-data";

export default function OmbudsmanFinderPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<typeof OMBUDSMAN_OFFICES[0] | null | undefined>(undefined);

  const search = () => {
    const q = query.trim().toLowerCase();
    if (!q) return;
    const centerName = CITY_TO_CENTER[q];
    const office = centerName
      ? OMBUDSMAN_OFFICES.find((o) => o.center === centerName)
      : OMBUDSMAN_OFFICES.find((o) => o.statesCovered.some((s) => s.toLowerCase().includes(q)));
    setResult(office || null);
  };

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <MapPin size={22} style={{ color: "#A78BFA" }} /> Ombudsman Jurisdiction Finder
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Filing at the wrong Insurance Ombudsman office is a real, avoidable reason for a complaint to be
          rejected on a technicality. Find the correct office for your city or state.
        </p>
      </div>

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="relative">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            className="input pl-10"
            placeholder="Enter your city or state (e.g. Kochi, Kerala)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
            suppressHydrationWarning
          />
        </div>
        <button onClick={search} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>Find my Ombudsman office</button>
      </div>

      {result === null && (
        <div className="card p-6 text-sm text-center" style={{ color: "var(--text-tertiary)", background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          No match found for "{query}". Try your state name, or a nearby major city.
        </div>
      )}

      {result && (
        <div className="card p-6 space-y-3" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Office of the Insurance Ombudsman, {result.center}</h3>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Covers: {result.statesCovered.join(", ")}
          </p>
          <div className="flex items-start gap-2 pt-2" style={{ borderTop: "1px solid var(--surface-5)" }}>
            <MapPin size={14} className="mt-0.5 shrink-0" style={{ color: "var(--text-tertiary)" }} />
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{result.address}</p>
          </div>
          <div className="flex items-center gap-2">
            <Mail size={14} className="shrink-0" style={{ color: "var(--text-tertiary)" }} />
            <a href={`mailto:${result.email}`} className="text-sm font-medium" style={{ color: "#A78BFA" }}>{result.email}</a>
          </div>
          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            Verify against cioins.co.in before filing — jurisdictions are occasionally revised by the Council for Insurance Ombudsman.
          </p>
        </div>
      )}
    </div>
  );
}
