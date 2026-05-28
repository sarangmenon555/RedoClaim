"use client";
import { useState, useEffect } from "react";
import { analysisApi } from "@/lib/api";
import { ExternalLink, CheckCircle, AlertTriangle, Info, Monitor, Scale } from "lucide-react";

export default function EdaakhilPage() {
  const [guide, setGuide] = useState<any>(null);

  useEffect(() => {
    analysisApi.edaakhilGuide().then((r) => setGuide(r.data)).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">e-Jagriti — Consumer Court Filing</h2>
        <p className="style-text-tertiary text-sm mt-1">
          File online at the Consumer Court if your insurer doesn't respond within 15 days.
        </p>
      </div>

      {/* Trigger banner */}
      <div className="card p-5 bg-surface-2 border-red-500\/20">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-red-600 shrink-0" size={18} />
          <div>
            <p className="font-semibold text-red-800">When to use e-Jagriti</p>
            <p className="text-sm text-red-700 mt-1">
              {guide?.when_to_use || "If your insurer has not responded within 15 days of your complaint, you can file directly on e-Jagriti Consumer Court portal under Section 2(11) of the Consumer Protection Act, 2019 — Deficiency in Service."}
            </p>
            <div className="flex gap-3 mt-3 flex-wrap">
              <a href="https://e-jagriti.gov.in" target="_blank" rel="noopener noreferrer"
                className="btn-primary text-sm px-4 py-2">
                Open e-Jagriti Portal <ExternalLink size={13} />
              </a>
              <a href="https://bimabharosa.irdai.gov.in/" target="_blank" rel="noopener noreferrer"
                className="btn-secondary text-sm px-4 py-2">
                Bima Bharosa Portal <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Legal basis */}
      <div className="card p-5 border-l-4 border-amber-500">
        <div className="flex items-start gap-3">
          <Scale className="text-amber-600 shrink-0" size={18} />
          <div>
            <p className="font-semibold style-text-primary">Legal Basis — Consumer Protection Act 2019</p>
            <p className="text-sm style-text-secondary mt-1">
              <strong>Section 2(11) — Deficiency in Service:</strong> An insurance company that unreasonably rejects a
              legitimate claim, delays settlement beyond 30 days, or fails to respond to your complaint within 15 days
              has committed a "Deficiency in Service." This entitles you to relief from the Consumer Court including
              the full claim amount, interest, and compensation for mental harassment.
            </p>
          </div>
        </div>
      </div>

      {/* Forum selection */}
      <div className="card p-5">
        <h3 className="font-semibold style-text-primary mb-4">Which Consumer Forum to approach?</h3>
        <div className="space-y-3">
          {[
            { forum: "District Consumer Disputes Redressal Commission", amount: "Up to ₹50 Lakhs", note: "Most health insurance claims" },
            { forum: "State Consumer Disputes Redressal Commission", amount: "₹50 Lakhs - ₹2 Crores", note: "Large commercial/corporate claims" },
            { forum: "National Consumer Disputes Redressal Commission", amount: "Above ₹2 Crores", note: "Major institutional claims" },
          ].map(({ forum, amount, note }) => (
            <div key={forum} className="flex items-start gap-3 p-3 bg-surface-2 rounded-lg">
              <div className="w-2 h-2 bg-violet-500 rounded-full mt-1.5 shrink-0" />
              <div>
                <p className="font-medium style-text-primary text-sm">{forum}</p>
                <p className="text-xs text-violet-400">{amount}</p>
                <p className="text-xs style-text-tertiary">{note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Step-by-step */}
      {guide?.steps && (
        <div className="card p-5">
          <h3 className="font-semibold style-text-primary mb-4 flex items-center gap-2">
            <Monitor size={16} className="text-violet-400" /> Step-by-step: How to file on e-Jagriti
          </h3>
          <div className="space-y-4">
            {guide.steps.map((s: any) => (
              <div key={s.step} className="flex items-start gap-4">
                <div className="w-8 h-8 bg-violet-500 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">{s.step}</div>
                <div>
                  <p className="font-medium style-text-primary text-sm">{s.action}</p>
                  <p className="text-sm style-text-tertiary mt-0.5">{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relief available */}
      {guide?.relief_you_can_claim && (
        <div className="card p-5">
          <h3 className="font-semibold style-text-primary mb-3">Relief you can claim</h3>
          <ul className="space-y-2">
            {guide.relief_you_can_claim.map((r: string) => (
              <li key={r} className="flex items-start gap-2 text-sm style-text-secondary">
                <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />{r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Important notes */}
      {guide?.important_notes && (
        <div className="card p-5 bg-surface-2">
          <div className="flex items-center gap-2 mb-3">
            <Info size={15} className="style-text-tertiary" />
            <h3 className="font-semibold style-text-secondary">Important notes</h3>
          </div>
          <ul className="space-y-1.5">
            {guide.important_notes.map((n: string) => (
              <li key={n} className="text-xs style-text-tertiary flex items-start gap-2">
                <span className="w-1 h-1 bg-surface-5 rounded-full mt-1.5 shrink-0" />{n}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
