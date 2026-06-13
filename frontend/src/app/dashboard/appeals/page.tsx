"use client";
import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { appealsApi, claimsApi } from "@/lib/api";
import toast from "react-hot-toast";
import {
  FileText, Loader2, Download, Copy, CheckCircle,
  Building2, Scale, Shield, Monitor, ArrowRight, AlertTriangle, Info
} from "lucide-react";
import type { AppealType, Claim } from "@/types";
import { DisclaimerBanner, LetterDisclaimer, AIOutputLabel } from "@/components/shared/DisclaimerBanner";

const APPEAL_TYPES = [
  {
    type: "gro" as AppealType,
    label: "GRO Appeal",
    desc: "Grievance Redressal Officer of the insurer",
    icon: Building2,
    activeColor: "border-violet-500 bg-surface-2",
    borderColor: "border-surface-4 hover:border-blue-300",
    step: "First step — file within 15 days of rejection",
    regulation: "IRDAI Master Circular 2024",
  },
  {
    type: "insurer_escalation" as AppealType,
    label: "CEO Escalation",
    desc: "Directly to the insurer's CEO / CMD",
    icon: Building2,
    activeColor: "border-surface-5 bg-surface-2",
    borderColor: "border-surface-4 hover:border-slate-400",
    step: "Run in parallel with GRO",
    regulation: "Escalation best practice",
  },
  {
    type: "ombudsman" as AppealType,
    label: "Ombudsman Complaint",
    desc: "Insurance Ombudsman (up to Rs.50 Lakhs)",
    icon: Scale,
    activeColor: "border-green-500 bg-surface-2",
    borderColor: "border-surface-4 hover:border-green-300",
    step: "If GRO fails within 30 days",
    regulation: "Insurance Ombudsman Rules 2017",
  },
  {
    type: "bima_bharosa" as AppealType,
    label: "Bima Bharosa",
    desc: "IRDAI online grievance portal",
    icon: Shield,
    activeColor: "border-amber-500 bg-surface-2",
    borderColor: "border-surface-4 hover:border-amber-300",
    step: "File at igms.irda.gov.in",
    regulation: "IRDAI Bima Bharosa system",
  },
  {
    type: "consumer_court" as AppealType,
    label: "Consumer Court (E-Daakhil)",
    desc: "District Consumer Court online",
    icon: Monitor,
    activeColor: "border-red-500 bg-surface-2",
    borderColor: "border-surface-4 hover:border-red-400",
    step: "Final escalation — edaakhil.nic.in",
    regulation: "Consumer Protection Act 2019",
  },
];

export default function AppealsPage() {
  const searchParams = useSearchParams();
  const claimIdParam = searchParams.get("claim_id");

  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState(claimIdParam || "");
  const [selectedType, setSelectedType] = useState<AppealType>("gro");
  const [additionalContext, setAdditionalContext] = useState("");
  const [letter, setLetter] = useState("");
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    claimsApi.list().then((r) => {
      setClaims(r.data);
      if (!selectedClaimId && r.data.length > 0) setSelectedClaimId(r.data[0].id);
    }).catch(() => {});
  }, []);

  const selectedClaim = claims.find((c) => c.id === selectedClaimId);

  const generateAppeal = async () => {
    if (!selectedClaimId) {
      toast.error("Select a claim first. Run a rejection audit to create one.");
      return;
    }
    setGenerating(true);
    setLetter("");
    try {
      const res = await appealsApi.generate(selectedClaimId, selectedType, additionalContext);
      setLetter(res.data.letter);
      toast.success("Draft generated. Please review carefully before sending.");
    } catch (e: any) {
      const detail = e?.response?.data?.detail || "Generation failed";
      toast.error(detail);
      if (detail.includes("audit")) toast("Run a rejection audit first", { icon: "ℹ️" });
    } finally {
      setGenerating(false);
    }
  };

  const copyLetter = () => {
    navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copied! Remember to review before sending.");
  };

  const downloadLetter = () => {
    const blob = new Blob([letter], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedType}_draft_letter.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const selectedAppeal = APPEAL_TYPES.find((t) => t.type === selectedType);

  // Check if selected claim has missing key fields
  const missingFields: string[] = [];
  if (selectedClaim) {
    if (!selectedClaim.policy_number) missingFields.push("policy number");
    if (!selectedClaim.claim_amount) missingFields.push("claim amount");
    if (!selectedClaim.rejection_date) missingFields.push("rejection date");
  }

  return (
    <div className="max-w-5xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">Appeal Draft Generator</h2>
        <p className="style-text-tertiary text-sm mt-1">
          AI generates draft appeal letters. <strong>Review carefully before sending.</strong>
        </p>
      </div>

      <DisclaimerBanner variant="banner" context="appeal" />

      <div className="grid md:grid-cols-3 gap-6">
        {/* Left: config */}
        <div className="md:col-span-1 space-y-4">

          {/* Claim selector */}
          <div className="card p-4">
            <label className="label">Select Claim</label>
            {claims.length === 0 ? (
              <div className="text-sm style-text-tertiary text-center py-3">
                No claims yet. Run a rejection audit first.
              </div>
            ) : (
              <select className="input" value={selectedClaimId}
                onChange={(e) => { setSelectedClaimId(e.target.value); setLetter(""); }}>
                <option value="">Choose a claim...</option>
                {claims.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.insurer_name}{c.claim_amount ? ` • Rs.${(c.claim_amount / 100000).toFixed(1)}L` : ""}
                    {c.rejection_date ? ` • ${new Date(c.rejection_date).toLocaleDateString("en-IN")}` : ""}
                  </option>
                ))}
              </select>
            )}

            {/* Show selected claim details */}
            {selectedClaim && (
              <div className="mt-3 p-3 bg-surface-2 rounded-lg text-xs space-y-1">
                <p className="font-semibold style-text-secondary mb-1">Claim details used in letter:</p>
                <div className="flex justify-between">
                  <span className="style-text-tertiary">Insurer</span>
                  <span className="style-text-primary font-medium">{selectedClaim.insurer_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="style-text-tertiary">Policy No.</span>
                  <span className={`font-medium ${selectedClaim.policy_number ? "style-text-primary" : "text-amber-600"}`}>
                    {selectedClaim.policy_number || "Not set"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="style-text-tertiary">Claim amount</span>
                  <span className={`font-medium ${selectedClaim.claim_amount ? "style-text-primary" : "text-amber-600"}`}>
                    {selectedClaim.claim_amount ? `Rs. ${selectedClaim.claim_amount.toLocaleString("en-IN")}` : "Not set"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="style-text-tertiary">Rejection date</span>
                  <span className={`font-medium ${selectedClaim.rejection_date ? "style-text-primary" : "text-amber-600"}`}>
                    {selectedClaim.rejection_date
                      ? new Date(selectedClaim.rejection_date).toLocaleDateString("en-IN")
                      : "Not set"}
                  </span>
                </div>
              </div>
            )}

            {/* Warning if key fields missing */}
            {missingFields.length > 0 && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                <AlertTriangle size={12} className="text-amber-600 mt-0.5 shrink-0" />
                <p className="text-xs text-amber-800">
                  Missing: {missingFields.join(", ")}. Re-run the audit with these fields filled in for a better letter.
                </p>
              </div>
            )}
          </div>

          {/* Appeal type */}
          <div className="card p-4">
            <label className="label mb-3 block">Letter Type</label>
            <div className="space-y-2">
              {APPEAL_TYPES.map(({ type, label, icon: Icon, borderColor, activeColor, step }) => (
                <button key={type} onClick={() => setSelectedType(type)}
                  className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                    selectedType === type ? activeColor : borderColor
                  }`}>
                  <div className="flex items-center gap-2 mb-0.5">
                    <Icon size={14} className="style-text-secondary shrink-0" />
                    <span className="font-medium style-text-primary text-sm">{label}</span>
                  </div>
                  <p className="text-xs style-text-tertiary ml-5">{step}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Context */}
          <div className="card p-4">
            <label className="label">Additional details (optional)</label>
            <textarea className="input h-20 resize-none"
              placeholder="Any specific facts to emphasize, e.g. 'Doctor confirmed medical necessity in writing on 5 June'"
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)} />
            <p className="text-xs style-text-tertiary mt-1">
              Add specific facts here to make the letter more precise and personal.
            </p>
          </div>

          <button onClick={generateAppeal} disabled={generating || !selectedClaimId}
            className="btn-primary w-full justify-center">
            {generating
              ? <><Loader2 size={15} className="animate-spin" /> Drafting...</>
              : <><FileText size={15} /> Generate Draft <ArrowRight size={13} /></>}
          </button>

          {/* Tip about name */}
          <div className="flex items-start gap-2 p-3 bg-surface-2 rounded-lg border border-surface-4">
            <Info size={12} className="text-violet-400 mt-0.5 shrink-0" />
            <p className="text-xs style-text-tertiary">
              Your name in the letter comes from your account profile. Update it in Settings if it shows as "Demo User".
            </p>
          </div>
        </div>

        {/* Right: letter output */}
        <div className="md:col-span-2">
          {!letter && !generating && (
            <div className="card p-12 text-center h-full flex flex-col items-center justify-center gap-4">
              <FileText className="style-text-tertiary" size={56} />
              <div>
                <p className="font-semibold style-text-secondary">Your draft letter will appear here</p>
                <p className="text-sm style-text-tertiary mt-1">AI-generated draft — always review before sending</p>
              </div>
            </div>
          )}

          {generating && (
            <div className="card p-12 text-center h-full flex flex-col items-center justify-center gap-4">
              <Loader2 className="animate-spin text-violet-400" size={40} />
              <div>
                <p className="font-semibold style-text-primary">Drafting your {selectedAppeal?.label}...</p>
                <p className="text-sm style-text-tertiary mt-1">Composing your letter...</p>
              </div>
            </div>
          )}

          {letter && (
            <div className="card overflow-hidden">
              {/* Header */}
              <div className="p-4 border-b border-surface-4 flex items-center justify-between bg-surface-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="text-green-600" size={15} />
                  <span className="font-medium style-text-primary text-sm">
                    {selectedAppeal?.label} — AI Draft
                  </span>
                  <AIOutputLabel />
                </div>
                <div className="flex gap-2">
                  <button onClick={copyLetter} className="btn-secondary text-xs px-3 py-1.5">
                    {copied ? <><CheckCircle size={12} /> Copied!</> : <><Copy size={12} /> Copy</>}
                  </button>
                  <button onClick={downloadLetter} className="btn-secondary text-xs px-3 py-1.5">
                    <Download size={12} /> Download
                  </button>
                </div>
              </div>

              {/* Review checklist */}
              <div className="p-4 bg-surface-2 border-b border-amber-500\/20">
                <p className="text-xs font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
                  <AlertTriangle size={12} /> Review checklist before sending:
                </p>
                <ul className="space-y-1">
                  {[
                    "Your full name is correct",
                    "Policy number and claim number are accurate",
                    "Insurer name and address are correct",
                    "Claim amount matches your records",
                    "Rejection date is accurate",
                    "All IRDAI regulation citations look relevant",
                    "No placeholder text like [NAME] or [DATE] remains",
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-xs text-amber-800">
                      <input type="checkbox" className="w-3 h-3 accent-amber-600" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Letter content */}
              <div className="p-6">
                <pre className="whitespace-pre-wrap text-sm style-text-secondary font-mono leading-relaxed">
                  {letter}
                </pre>
              </div>

              <LetterDisclaimer />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}