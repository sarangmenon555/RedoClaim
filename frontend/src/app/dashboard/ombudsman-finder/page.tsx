"use client";
import { useState } from "react";
import { MapPin, Mail, Phone } from "lucide-react";
import { OMBUDSMAN_OFFICES, STATES_AND_UTS } from "@/lib/ombudsman-data";

const STATES = STATES_AND_UTS.filter((s) => s.type === "State");
const UNION_TERRITORIES = STATES_AND_UTS.filter((s) => s.type === "Union Territory");

export default function OmbudsmanFinderPage() {
  const [selected, setSelected] = useState("");
  const [searched, setSearched] = useState("");

  const entry = STATES_AND_UTS.find((s) => s.name === searched);
  const offices = entry
    ? entry.centers
        .map((c) => OMBUDSMAN_OFFICES.find((o) => o.center === c))
        .filter((o): o is (typeof OMBUDSMAN_OFFICES)[0] => Boolean(o))
    : [];

  const search = () => {
    if (!selected) return;
    setSearched(selected);
  };

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <MapPin size={22} style={{ color: "#A78BFA" }} /> Ombudsman Jurisdiction Finder
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Filing at the wrong Insurance Ombudsman office is a real, avoidable reason for a complaint to be
          rejected on a technicality. Find the correct office for your State or Union Territory.
        </p>
      </div>

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div className="space-y-2">
          <label htmlFor="state-ut" className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            State / UT
          </label>
          <select
            id="state-ut"
            className="input"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            suppressHydrationWarning
          >
            <option value="">Select your State / UT</option>
            <optgroup label="States">
              {STATES.map((s) => (
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </optgroup>
            <optgroup label="Union Territories">
              {UNION_TERRITORIES.map((s) => (
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </optgroup>
          </select>
        </div>
        <button
          onClick={search}
          disabled={!selected}
          className="btn-primary w-full justify-center py-3"
          suppressHydrationWarning
        >
          Find my Ombudsman office
        </button>
      </div>

      {entry && offices.length === 0 && (
        <div className="card p-6 text-sm text-center" style={{ color: "var(--text-tertiary)", background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          No Ombudsman office is listed for {entry.name}. Verify on cioins.co.in.
        </div>
      )}

      {entry && entry.note && (
        <div className="card p-4 text-sm" style={{ color: "var(--text-secondary)", background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          {entry.note}
        </div>
      )}

      {offices.map((office) => (
        <div key={office.center} className="card p-6 space-y-3" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Office of the Insurance Ombudsman, {office.center}</h3>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Covers: {office.statesCovered.join(", ")}
          </p>
          <div className="flex items-start gap-2 pt-2" style={{ borderTop: "1px solid var(--surface-5)" }}>
            <MapPin size={14} className="mt-0.5 shrink-0" style={{ color: "var(--text-tertiary)" }} />
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{office.address}</p>
          </div>
          <div className="flex items-center gap-2">
            <Mail size={14} className="shrink-0" style={{ color: "var(--text-tertiary)" }} />
            <a href={`mailto:${office.email}`} className="text-sm font-medium" style={{ color: "#A78BFA" }}>{office.email}</a>
          </div>
          {office.phone && (
            <div className="flex items-center gap-2">
              <Phone size={14} className="shrink-0" style={{ color: "var(--text-tertiary)" }} />
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{office.phone}</span>
            </div>
          )}
        </div>
      ))}

      {entry && offices.length > 0 && (
        <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
          Verify against cioins.co.in before filing — jurisdictions are occasionally revised by the Council for Insurance Ombudsman.
        </p>
      )}
    </div>
  );
}
