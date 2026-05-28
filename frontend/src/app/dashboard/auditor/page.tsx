"use client";
import { useState, useEffect, useCallback, Suspense } from "react";
import { useDropzone } from "react-dropzone";
import { useSearchParams } from "next/navigation";
import { documentsApi, analysisApi } from "@/lib/api";
import toast from "react-hot-toast";
import {
  Upload, AlertTriangle, CheckCircle, XCircle, Shield,
  Scale, ArrowRight, Loader2, ExternalLink, Info,
  Clock, FileText, ChevronDown, ChevronUp, Banknote
} from "lucide-react";
import type { Document } from "@/types";
import Link from "next/link";

type Step = "upload" | "form" | "analyzing" | "result";

// useSearchParams must be inside a Suspense boundary in Next.js app router
function AuditorPageInner() {
  const searchParams = useSearchParams();

  const [step, setStep] = useState<Step>("upload");
  const [rejectionDoc, setRejectionDoc] = useState<Document | null>(null);
  const [policyDocs, setPolicyDocs] = useState<Document[]>([]);
  const [cisDocs, setCisDocs] = useState<Document[]>([]);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    sla: true, violations: true, moratorium: true, deficiency: true, escalation: true,
  });

  const [form, setForm] = useState({
    insurerName: "", policyNumber: "", claimAmount: "",
    insuranceType: "health", policyDocumentId: "", cisDocumentId: "",
    claimDate: "", rejectionDate: "", groFiled: false, groFiledDate: "",
  });

  // Load all user documents for policy/CIS dropdowns
  useEffect(() => {
    documentsApi.list().then((r) => {
      const all: Document[] = r.data;
      setPolicyDocs(all.filter((d) => d.doc_type === "policy" && d.ocr_status === "done"));
      setCisDocs(all.filter((d) => d.doc_type === "other" && d.ocr_status === "done"));
    }).catch(() => {});
  }, []);

  // ── FIX: Load existing document if ?doc= param is present ──────
  useEffect(() => {
    const docId = searchParams.get("doc");
    if (!docId) return;

    setLoadingDoc(true);

    const tryLoad = async () => {
      try {
        const res = await documentsApi.get(docId);
        const doc: Document = res.data;

        if (doc.ocr_status === "done") {
          setRejectionDoc(doc);
          setStep("form");
          toast.success(`"${doc.file_name}" loaded. Fill in claim details to start audit.`);
          setLoadingDoc(false);
        } else if (doc.ocr_status === "failed") {
          toast.error("Document OCR failed. Please re-upload.");
          setLoadingDoc(false);
        } else {
          // Still processing — poll until done
          toast("Document is still processing, waiting...", { icon: "⏳" });
          const interval = setInterval(async () => {
            try {
              const r = await documentsApi.get(docId);
              if (r.data.ocr_status === "done") {
                setRejectionDoc(r.data);
                setStep("form");
                clearInterval(interval);
                setLoadingDoc(false);
                toast.success("Ready. Fill in claim details to start audit.");
              } else if (r.data.ocr_status === "failed") {
                clearInterval(interval);
                setLoadingDoc(false);
                toast.error("Document OCR failed. Please re-upload.");
              }
            } catch {
              clearInterval(interval);
              setLoadingDoc(false);
            }
          }, 3000);
          // Give up after 2 minutes
          setTimeout(() => {
            clearInterval(interval);
            setLoadingDoc(false);
          }, 120000);
        }
      } catch {
        toast.error("Could not load document. Please re-upload.");
        setLoadingDoc(false);
      }
    };

    tryLoad();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // ────────────────────────────────────────────────────────────────

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "application/pdf": [".pdf"], "image/*": [] },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
    disabled: uploading || loadingDoc,
    onDrop: useCallback(async (files: File[]) => {
      const file = files[0];
      if (!file) return;
      setUploading(true);
      try {
        const res = await documentsApi.upload(file, "rejection_letter", form.insuranceType);
        const docId = res.data.document_id;
        toast.success("Rejection letter uploaded. OCR processing...");
        const interval = setInterval(async () => {
          try {
            const docRes = await documentsApi.get(docId);
            if (docRes.data.ocr_status === "done") {
              setRejectionDoc(docRes.data);
              clearInterval(interval);
              setStep("form");
              toast.success("Ready. Fill in claim details to start audit.");
            } else if (docRes.data.ocr_status === "failed") {
              clearInterval(interval);
              toast.error("OCR failed. Please try a clearer image or PDF.");
            }
          } catch { /* keep polling */ }
        }, 3000);
        setTimeout(() => clearInterval(interval), 120000);
      } catch (e: any) {
        toast.error(e?.response?.data?.detail || "Upload failed");
      } finally {
        setUploading(false);
      }
    }, [form.insuranceType]),
  });

  const runAudit = async () => {
    if (!rejectionDoc) {
      toast.error("No rejection document loaded");
      return;
    }
    if (!form.insurerName.trim()) {
      toast.error("Fill in insurer name at minimum");
      return;
    }
    setStep("analyzing");
    try {
      const res = await analysisApi.auditRejection({
        rejection_document_id: rejectionDoc.id,
        policy_document_id: form.policyDocumentId || undefined,
        cis_document_id: form.cisDocumentId || undefined,
        insurer_name: form.insurerName,
        policy_number: form.policyNumber,
        claim_amount: form.claimAmount ? parseFloat(form.claimAmount) : undefined,
        insurance_type: form.insuranceType,
        claim_date: form.claimDate || undefined,
        rejection_date: form.rejectionDate || undefined,
        gro_filed: form.groFiled,
        gro_filed_date: form.groFiledDate || undefined,
      });
      setAuditResult(res.data);
      setStep("result");
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail?.includes("still processing")) {
        toast.error("Document is still being processed. Please wait a moment and try again.");
      } else {
        toast.error(detail || "Audit failed. Please try again.");
      }
      setStep("form");
    }
  };

  const toggle = (k: string) => setExpandedSections(p => ({ ...p, [k]: !p[k] }));

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">Claim Rejection Auditor</h2>
        <p className="style-text-tertiary text-sm mt-1">
          AI audits your rejection against IRDAI Master Circular 2024 using the Hierarchy of Evidence.
        </p>
      </div>

      {/* Hierarchy of Evidence info */}
      <div className="card p-4 bg-surface-2 border-violet-500/20">
        <p className="text-xs font-semibold style-text-secondary mb-2">IRDAI Hierarchy of Evidence</p>
        <div className="flex gap-4 text-xs text-violet-400 flex-wrap">
          {["Step 1: SLA/TAT violations", "Step 2: Master Circular 2024 violations", "Step 3: Redressal route"].map((s, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <span className="w-5 h-5 bg-violet-500 text-white rounded-full flex items-center justify-center font-bold text-xs">{i+1}</span>
              {s.replace(/Step \d: /, "")}
            </div>
          ))}
        </div>
      </div>

      {/* Loading existing doc from ?doc= param */}
      {loadingDoc && (
        <div className="card p-8 text-center">
          <Loader2 className="animate-spin text-violet-400 mx-auto mb-3" size={32} />
          <p className="font-medium style-text-secondary">Loading your document...</p>
          <p className="text-xs style-text-tertiary mt-1">Waiting for OCR to complete</p>
        </div>
      )}

      {!loadingDoc && step === "upload" && (
        <div
          {...getRootProps()}
          className={`card border-2 border-dashed p-12 text-center cursor-pointer transition-all ${
            isDragActive ? "border-red-400 bg-surface-2" : "border-surface-5 hover:border-red-400"
          }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="animate-spin text-red-500" size={32} />
              <p className="font-medium style-text-secondary">Processing rejection letter via OCR...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 bg-surface-2 rounded-2xl flex items-center justify-center">
                <Upload className="text-red-500" size={28} />
              </div>
              <p className="font-semibold style-text-primary">Upload your rejection letter</p>
              <p className="text-sm style-text-tertiary">PDF or image from your insurer</p>
            </div>
          )}
        </div>
      )}

      {!loadingDoc && step === "form" && rejectionDoc && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-4 flex items-center gap-3 bg-surface-2 border-neon-500\/20">
            <CheckCircle className="text-green-600 shrink-0" size={18} />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-green-800 text-sm truncate">Document ready: {rejectionDoc.file_name}</p>
              <p className="text-xs text-green-600">OCR complete — fill details for IRDAI audit</p>
            </div>
            <button
              onClick={() => { setRejectionDoc(null); setStep("upload"); }}
              className="text-xs style-text-tertiary hover:text-red-500 transition shrink-0"
            >
              Change
            </button>
          </div>

          <div className="card p-6 space-y-4">
            <h3 className="font-semibold style-text-primary">Claim details</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="label">Insurer name *</label>
                <input className="input" placeholder="e.g. Star Health Insurance"
                  value={form.insurerName} onChange={(e) => setForm({...form, insurerName: e.target.value})} />
              </div>
              <div>
                <label className="label">Policy number</label>
                <input className="input" placeholder="e.g. P/211115/01/2024/001234"
                  value={form.policyNumber} onChange={(e) => setForm({...form, policyNumber: e.target.value})} />
              </div>
              <div>
                <label className="label">Claim amount (₹)</label>
                <input className="input" type="number" placeholder="e.g. 500000"
                  value={form.claimAmount} onChange={(e) => setForm({...form, claimAmount: e.target.value})} />
              </div>
              <div>
                <label className="label">Insurance type</label>
                <select className="input" value={form.insuranceType}
                  onChange={(e) => setForm({...form, insuranceType: e.target.value})}>
                  <option value="health">Health Insurance</option>
                  <option value="motor">Motor Insurance</option>
                </select>
              </div>
              <div>
                <label className="label">Claim date</label>
                <input className="input" type="date" value={form.claimDate}
                  onChange={(e) => setForm({...form, claimDate: e.target.value})} />
              </div>
              <div>
                <label className="label">Rejection date</label>
                <input className="input" type="date" value={form.rejectionDate}
                  onChange={(e) => setForm({...form, rejectionDate: e.target.value})} />
              </div>
              {policyDocs.length > 0 && (
                <div>
                  <label className="label">Policy document (improves accuracy)</label>
                  <select className="input" value={form.policyDocumentId}
                    onChange={(e) => setForm({...form, policyDocumentId: e.target.value})}>
                    <option value="">None selected</option>
                    {policyDocs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
                  </select>
                </div>
              )}
              {cisDocs.length > 0 && (
                <div>
                  <label className="label">CIS document (for exclusion check)</label>
                  <select className="input" value={form.cisDocumentId}
                    onChange={(e) => setForm({...form, cisDocumentId: e.target.value})}>
                    <option value="">None selected</option>
                    {cisDocs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
                  </select>
                </div>
              )}
              <div className="md:col-span-2 flex items-center gap-3">
                <input type="checkbox" id="gro" checked={form.groFiled}
                  onChange={(e) => setForm({...form, groFiled: e.target.checked})}
                  className="w-4 h-4 accent-violet-500" />
                <label htmlFor="gro" className="text-sm style-text-secondary">I have already filed a GRO complaint</label>
              </div>
              {form.groFiled && (
                <div>
                  <label className="label">GRO complaint date</label>
                  <input className="input" type="date" value={form.groFiledDate}
                    onChange={(e) => setForm({...form, groFiledDate: e.target.value})} />
                </div>
              )}
            </div>
            <div className="flex gap-3 pt-2">
              <button onClick={runAudit} className="btn-primary">
                Run IRDAI Audit <ArrowRight size={15} />
              </button>
              <button onClick={() => { setRejectionDoc(null); setStep("upload"); }} className="btn-secondary">
                Re-upload
              </button>
            </div>
          </div>
        </div>
      )}

      {step === "analyzing" && (
        <div className="card p-12 text-center">
          <Loader2 className="animate-spin text-violet-400 mx-auto mb-4" size={40} />
          <p className="font-semibold style-text-primary mb-3">Running IRDAI Hierarchy of Evidence Audit...</p>
          <div className="text-sm style-text-tertiary space-y-1.5 text-left max-w-xs mx-auto">
            <p className="text-green-600">✓ OCR complete</p>
            <p className="text-green-600">✓ RAG: retrieving IRDAI regulations from Qdrant</p>
            <p className="text-blue-500 animate-pulse">⟳ Step 1: Checking SLA/TAT violations...</p>
            <p className="style-text-tertiary">⟳ Step 2: deepseek-r1 legal reasoning (local)...</p>
            <p className="style-text-tertiary">⟳ Step 3: Determining redressal route...</p>
          </div>
        </div>
      )}

      {step === "result" && auditResult && (
        <AuditResultView result={auditResult} toggle={toggle} expandedSections={expandedSections} />
      )}
    </div>
  );
}

export default function AuditorPage() {
  return (
    <Suspense fallback={
      <div className="max-w-4xl flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-violet-400" size={32} />
      </div>
    }>
      <AuditorPageInner />
    </Suspense>
  );
}

function AuditResultView({ result, toggle, expandedSections }: any) {
  const { summary, report } = result;
  const hoe = report?.hierarchy_of_evidence;
  const sla = hoe?.step1_sla;
  const reg = hoe?.step2_regulations;
  const esc = hoe?.step3_redressal;
  const audit = reg?.audit || {};
  const moratorium = reg?.moratorium || {};
  const deficiency = reg?.deficiency_in_service || {};
  const cis = reg?.cis_check || {};
  const portability = report?.portability_advice;

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Verdict */}
      <div className={`card p-6 border-l-4 ${!summary.is_valid_rejection ? "border-red-500 bg-surface-2" : "border-green-500 bg-surface-2"}`}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            {!summary.is_valid_rejection
              ? <XCircle className="text-red-600" size={28} />
              : <CheckCircle className="text-green-600" size={28} />}
            <div>
              <h3 className="text-lg font-bold style-text-primary">
                {!summary.is_valid_rejection ? "Rejection appears INVALID" : "Rejection appears valid"}
              </h3>
              <div className="flex flex-wrap gap-2 mt-1">
                {summary.sla_violations > 0 && <span className="badge-high">{summary.sla_violations} SLA Violation{summary.sla_violations > 1 ? "s" : ""}</span>}
                {summary.irdai_violations > 0 && <span className="badge-high">{summary.irdai_violations} IRDAI Violation{summary.irdai_violations > 1 ? "s" : ""}</span>}
                {summary.moratorium_shield && <span className="badge-low">Moratorium Shield</span>}
                {summary.deficiency_in_service && <span className="badge-medium">Deficiency in Service</span>}
                {summary.cis_violation && <span className="badge-high">CIS Violation</span>}
                {summary.interest_applicable && <span className="badge-medium">Interest Applicable</span>}
                {summary.edaakhil_applicable && <span className="badge-high">E-Daakhil NOW</span>}
              </div>
            </div>
          </div>
          <span className={`text-sm px-3 py-1.5 rounded-full font-semibold ${
            summary.strength_of_case === "strong" ? "bg-green-100 text-green-800" :
            summary.strength_of_case === "moderate" ? "bg-amber-100 text-amber-800" :
            "bg-red-100 text-red-800"
          }`}>
            {summary.strength_of_case?.toUpperCase()} CASE
          </span>
        </div>
      </div>

      {/* Step 1: SLA Violations */}
      <Accordion
        title={`Step 1 — SLA/TAT Violations (${sla?.violations_found || 0} found)`}
        icon={<Clock size={16} className="text-amber-500" />}
        expanded={expandedSections.sla}
        onToggle={() => toggle("sla")}
        badge={sla?.violations_found > 0 ? "high" : "low"}
        badgeText={sla?.violations_found > 0 ? "VIOLATIONS FOUND" : "COMPLIANT"}
      >
        {sla?.sla_violations?.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {sla.sla_violations.map((v: any, i: number) => (
              <div key={i} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium style-text-primary text-sm">{v.detail}</p>
                    <p className="text-xs text-violet-400 mt-1">📋 {v.regulation}</p>
                    {v.interest_applicable && (
                      <p className="text-xs text-amber-700 mt-1 font-medium">💰 {v.interest_note}</p>
                    )}
                    {v.edaakhil_trigger && (
                      <p className="text-xs text-red-700 mt-1 font-medium">
                        🚨 E-Daakhil filing now applicable — insurer GRO overdue
                      </p>
                    )}
                  </div>
                  <span className={`badge-${v.severity} shrink-0`}>{v.severity}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="p-4 text-sm style-text-tertiary">No SLA violations detected based on provided dates.</p>
        )}
        {sla?.interest_applicable && (
          <div className="p-4 bg-surface-2 border-t border-amber-500\/20 flex items-start gap-2">
            <Banknote size={15} className="text-amber-600 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-800">
              <strong>Interest demand:</strong> Under IRDAI Master Circular 2024, Para 7.4, the insurer must pay
              interest at Bank Rate + 2% per annum on the claim amount for every day of delay beyond 30 days.
              Include this in your appeal letter.
            </p>
          </div>
        )}
      </Accordion>

      {/* Step 2: IRDAI Regulatory Violations */}
      <Accordion
        title={`Step 2 — IRDAI Regulatory Violations (${audit?.step2_regulatory_violations?.length || 0} found)`}
        icon={<AlertTriangle size={16} className="text-red-500" />}
        expanded={expandedSections.violations}
        onToggle={() => toggle("violations")}
        badge={audit?.step2_regulatory_violations?.length > 0 ? "high" : "low"}
        badgeText={audit?.step2_regulatory_violations?.length > 0 ? "VIOLATIONS" : "NONE"}
      >
        {audit?.step2_regulatory_violations?.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {audit.step2_regulatory_violations.map((v: any, i: number) => (
              <div key={i} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium style-text-primary text-sm">{v.violation}</p>
                    <p className="text-xs text-violet-400 mt-1">📋 {v.regulation}</p>
                    {v.argument && <p className="text-xs style-text-tertiary mt-1 italic">{v.argument}</p>}
                  </div>
                  <span className={`badge-${v.severity} shrink-0`}>{v.severity}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="p-4 text-sm style-text-tertiary">No specific regulatory violations identified by AI.</p>
        )}
        {cis?.cis_violation && (
          <div className="p-4 bg-surface-2 border-t border-red-500\/20">
            <p className="text-xs font-semibold text-red-800 mb-1">CIS Violation — IRDAI Master Circular 2024, Para 4.2</p>
            <p className="text-xs text-red-700">{cis.argument}</p>
          </div>
        )}
      </Accordion>

      {/* Deficiency in Service */}
      {deficiency?.deficiency_in_service && (
        <div className="card p-5 border-l-4 border-amber-500 bg-surface-2">
          <div className="flex items-start gap-3">
            <Scale className="text-amber-600 shrink-0" size={18} />
            <div>
              <p className="font-semibold text-amber-900">Deficiency in Service — CPA 2019, Section 2(11)</p>
              <p className="text-sm text-amber-800 mt-1">{deficiency.statement}</p>
              {deficiency.product_liability_note && (
                <p className="text-xs text-amber-700 mt-2 italic">{deficiency.product_liability_note}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Moratorium Shield */}
      {moratorium?.moratorium_applies && (
        <div className="card p-5 border-l-4 border-violet-500 bg-surface-2">
          <div className="flex items-start gap-3">
            <Shield className="text-violet-400 shrink-0" size={18} />
            <div>
              <p className="font-semibold style-text-secondary">Moratorium Shield Active — IRDAI Health Regs 2024, Reg 8(6)</p>
              <p className="text-sm style-text-secondary mt-1">{moratorium.argument}</p>
              {moratorium.counter_to_insurer && (
                <p className="text-xs text-violet-400 mt-2 italic">💡 {moratorium.counter_to_insurer}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Key Arguments */}
      {audit?.key_arguments?.length > 0 && (
        <div className="card p-5">
          <h4 className="font-semibold style-text-primary mb-3 flex items-center gap-2">
            <Scale size={16} className="text-violet-400" /> Key legal arguments
          </h4>
          <ul className="space-y-2">
            {audit.key_arguments.map((arg: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm style-text-secondary">
                <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />
                {arg}
              </li>
            ))}
          </ul>
          {audit.evidence_needed?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-surface-4">
              <p className="text-xs font-semibold style-text-secondary mb-2">Evidence you should gather:</p>
              <ul className="space-y-1">
                {audit.evidence_needed.map((e: string, i: number) => (
                  <li key={i} className="text-xs style-text-tertiary flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-surface-5 rounded-full shrink-0" />{e}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Escalation */}
      <Accordion
        title="Step 3 — Redressal Path"
        icon={<ArrowRight size={16} className="text-green-600" />}
        expanded={expandedSections.escalation}
        onToggle={() => toggle("escalation")}
      >
        <div className="p-5 space-y-4">
          {esc?.recommended_immediate_action && (
            <div className="bg-surface-2 border border-red-500\/20 rounded-lg p-3">
              <p className="text-sm font-semibold text-red-800">⚡ Immediate action required:</p>
              <p className="text-sm text-red-700 mt-0.5">{esc.recommended_immediate_action}</p>
            </div>
          )}
          <div className="space-y-3">
            {esc?.escalation_path?.map((s: any) => (
              <div key={s.step} className="flex items-start gap-4">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                  s.eligible === false ? "bg-surface-3 style-text-tertiary" : "bg-violet-500 text-white"
                }`}>{s.step}</div>
                <div className="flex-1">
                  <p className="font-medium style-text-primary text-sm">{s.route}</p>
                  <p className="text-xs style-text-tertiary">{s.deadline} • {s.cost}</p>
                  <p className="text-xs style-text-tertiary mt-0.5">{s.how}</p>
                  {s.edaakhil_now_applicable && (
                    <div className="mt-1">
                      <a href="https://edaakhil.nic.in" target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-violet-400 font-medium hover:underline">
                        File on E-Daakhil now <ExternalLink size={10} />
                      </a>
                    </div>
                  )}
                  {s.relief_available && (
                    <ul className="mt-1 space-y-0.5">
                      {s.relief_available.slice(0, 3).map((r: string) => (
                        <li key={r} className="text-xs text-green-700 flex items-center gap-1">
                          <CheckCircle size={10} /> {r}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Accordion>

      {/* Portability */}
      {portability && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Info size={15} className="text-blue-500" />
            <h4 className="font-semibold style-text-primary">Portability Option</h4>
          </div>
          <p className="text-sm style-text-secondary mb-3">{portability.when_to_consider_porting}</p>
          <ul className="space-y-1.5">
            {portability.key_rights?.slice(0, 4).map((r: string, i: number) => (
              <li key={i} className="text-xs style-text-secondary flex items-start gap-2">
                <CheckCircle size={12} className="text-green-500 mt-0.5 shrink-0" />{r}
              </li>
            ))}
          </ul>
          <Link href="/dashboard/portability" className="text-xs text-violet-400 font-medium mt-3 inline-block hover:underline">
            Get full portability guide →
          </Link>
        </div>
      )}

      {/* CTA */}
      <div className="card p-5 bg-surface-2 border-violet-500/20">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="font-semibold style-text-primary">Generate your appeal letter</p>
            <p className="text-sm style-text-secondary">AI will cite every violation found above in the letter</p>
          </div>
          <Link href={`/dashboard/appeals?claim_id=${result.claim_id}`} className="btn-primary">
            Generate Appeal <ArrowRight size={15} />
          </Link>
        </div>
      </div>
    </div>
  );
}

function Accordion({ title, icon, expanded, onToggle, badge, badgeText, children }: any) {
  return (
    <div className="card overflow-hidden">
      <button className="w-full flex items-center justify-between p-5 hover:bg-surface-2 transition" onClick={onToggle}>
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold style-text-primary text-sm">{title}</span>
          {badge && badgeText && (
            <span className={`badge-${badge} text-xs`}>{badgeText}</span>
          )}
        </div>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {expanded && <div className="border-t border-surface-4">{children}</div>}
    </div>
  );
}