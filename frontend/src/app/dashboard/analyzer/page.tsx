"use client";
import { useState, useCallback, useEffect, Suspense } from "react";
import { useDropzone } from "react-dropzone";
import { useSearchParams } from "next/navigation";
import { documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import {
  Upload, FileText, CheckCircle, AlertTriangle, Clock,
  ChevronDown, ChevronUp, Info, Shield, Loader2
} from "lucide-react";
import type { Document, PolicyClauses, RiskFlag } from "@/types";
import { DisclaimerBanner, AIOutputLabel } from "@/components/shared/DisclaimerBanner";

function AnalyzerPageInner() {
  const searchParams = useSearchParams();
  const [uploading, setUploading] = useState(false);
  const [document, setDocument] = useState<Document | null>(null);
  const [polling, setPolling] = useState(false);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // ── Load existing doc if ?doc= param present (from Documents page) ──
  useEffect(() => {
    const docId = searchParams.get("doc");
    if (!docId) return;

    setLoadingDoc(true);

    const tryLoad = async () => {
      try {
        const res = await documentsApi.get(docId);
        const doc: Document = res.data;

        if (doc.ocr_status === "done" && doc.embedding_status === "done") {
          setDocument(doc);
          setLoadingDoc(false);
          toast.success(`"${doc.file_name}" loaded.`);
        } else if (doc.ocr_status === "failed") {
          setLoadingDoc(false);
          toast.error("Document analysis failed. Please re-upload.");
        } else {
          // Still processing — poll
          toast("Document is still being analyzed, please wait...", { icon: "⏳" });
          setPolling(true);
          const interval = setInterval(async () => {
            try {
              const r = await documentsApi.get(docId);
              if (r.data.ocr_status === "done" && r.data.embedding_status === "done") {
                setDocument(r.data);
                setPolling(false);
                setLoadingDoc(false);
                clearInterval(interval);
                toast.success("Analysis complete.");
              } else if (r.data.ocr_status === "failed") {
                clearInterval(interval);
                setPolling(false);
                setLoadingDoc(false);
                toast.error("Analysis failed. Please re-upload.");
              }
            } catch {
              clearInterval(interval);
              setPolling(false);
              setLoadingDoc(false);
            }
          }, 3000);
          setTimeout(() => {
            clearInterval(interval);
            setPolling(false);
            setLoadingDoc(false);
          }, 300000);
        }
      } catch {
        setLoadingDoc(false);
        toast.error("Could not load document.");
      }
    };

    tryLoad();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // ────────────────────────────────────────────────────────────────────

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await documentsApi.upload(file, "policy", "health");
      const docId = res.data.document_id;
      toast.success("Policy uploaded! AI analysis starting...");
      setPolling(true);
      const interval = setInterval(async () => {
        try {
          const docRes = await documentsApi.get(docId);
          const doc = docRes.data;
          if (doc.ocr_status === "done" && doc.embedding_status === "done") {
            setDocument(doc);
            setPolling(false);
            clearInterval(interval);
            toast.success("Analysis complete — review results carefully");
          } else if (doc.ocr_status === "failed") {
            setPolling(false);
            clearInterval(interval);
            toast.error("Analysis failed. Try again.");
          }
        } catch { /* keep polling */ }
      }, 3000);
      setTimeout(() => { clearInterval(interval); setPolling(false); }, 300000);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "image/*": [".jpg", ".jpeg", ".png"] },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
    disabled: uploading || polling || loadingDoc,
  });

  const toggle = (key: string) => setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  const clauses = document?.extracted_clauses as PolicyClauses | undefined;

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">Policy Analyzer</h2>
        <p className="style-text-tertiary text-sm mt-1">
          AI extracts key clauses from your policy PDF. Results are a starting point — verify against your original document.
        </p>
      </div>

      <DisclaimerBanner variant="banner" context="cis" />

      {/* Loading existing doc */}
      {loadingDoc && (
        <div className="card p-8 text-center">
          <Loader2 className="animate-spin text-violet-400 mx-auto mb-3" size={32} />
          <p className="font-medium style-text-secondary">Loading your policy...</p>
          <p className="text-xs style-text-tertiary mt-1">Waiting for analysis to complete</p>
        </div>
      )}

      {/* Upload zone — only show when no doc loaded and not loading */}
      {!document && !loadingDoc && (
        <div
          {...getRootProps()}
          className={`card border-2 border-dashed p-12 text-center cursor-pointer transition-all ${
            isDragActive ? "border-violet-400 bg-surface-2" : "border-surface-5 hover:border-violet-400 hover:bg-surface-2"
          } ${(uploading || polling) ? "pointer-events-none opacity-60" : ""}`}
        >
          <input {...getInputProps()} />
          {uploading || polling ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="animate-spin text-violet-400" size={36} />
              <p className="font-medium style-text-secondary">
                {uploading ? "Uploading..." : "Analyzing policy"}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 bg-surface-2 rounded-2xl flex items-center justify-center">
                <Upload className="text-violet-400" size={28} />
              </div>
              <div>
                <p className="font-semibold style-text-primary">
                  {isDragActive ? "Drop policy here" : "Drop policy PDF or click to upload"}
                </p>
                <p className="text-sm style-text-tertiary mt-1">PDF, JPG, PNG up to 50MB</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {document && clauses && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-5 flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-surface-2 rounded-lg flex items-center justify-center">
                <CheckCircle className="text-green-600" size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-semibold style-text-primary">{document.file_name}</p>
                  <AIOutputLabel />
                </div>
                <p className="text-sm style-text-tertiary">
                  {clauses.insurer_name} • Sum insured: {clauses.sum_insured}
                </p>
              </div>
            </div>
            <button onClick={() => setDocument(null)} className="btn-secondary text-xs px-3 py-1.5">
              Analyze another
            </button>
          </div>

          <div className="card p-4 border-amber-500\/20 bg-surface-2 flex items-start gap-3">
            <AlertTriangle size={15} className="text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 leading-relaxed">
              <strong>Verify this output.</strong> OCR and AI extraction can miss clauses, misread numbers,
              or misinterpret policy language. Always compare these results against your actual policy document.
              If a clause is missing here, it may still be in your policy.
            </div>
          </div>

          {clauses.plain_english_summary && (
            <div className="card p-5 border-l-4 border-violet-500">
              <div className="flex items-center gap-2 mb-2">
                <Info size={16} className="text-violet-400" />
                <span className="font-semibold style-text-primary">AI Summary</span>
                <AIOutputLabel />
              </div>
              <p className="text-sm style-text-secondary leading-relaxed">{clauses.plain_english_summary}</p>
            </div>
          )}

          {clauses.risky_clauses && clauses.risky_clauses.length > 0 && (
            <div className="card overflow-hidden">
              <button className="w-full flex items-center justify-between p-5 hover:bg-surface-2 transition"
                onClick={() => toggle("risks")}>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="text-red-500" size={18} />
                  <span className="font-semibold style-text-primary">
                    Potentially Risky Clauses ({clauses.risky_clauses.length})
                  </span>
                  <AIOutputLabel />
                </div>
                {expanded["risks"] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              {expanded["risks"] && (
                <div className="border-t divide-y divide-slate-100">
                  {clauses.risky_clauses.map((flag: RiskFlag, i: number) => (
                    <div key={i} className="p-4">
                      <p className="font-medium style-text-primary text-sm">{flag.clause}</p>
                      <p className="text-sm text-red-600 mt-1">{flag.why_risky}</p>
                      {flag.irdai_reference && (
                        <p className="text-xs style-text-tertiary mt-1">{flag.irdai_reference}</p>
                      )}
                    </div>
                  ))}
                  <div className="p-3 bg-surface-2 text-xs style-text-tertiary">
                    These are AI-identified potential risks. A clause flagged here may still be valid under your specific policy terms.
                  </div>
                </div>
              )}
            </div>
          )}

          {clauses.waiting_periods?.length > 0 && (
            <ClauseSection title={`Waiting Periods (${clauses.waiting_periods.length})`}
              icon={<Clock size={18} className="text-amber-500" />}
              isExpanded={expanded["waiting"]} onToggle={() => toggle("waiting")}>
              {clauses.waiting_periods.map((wp, i) => (
                <div key={i} className="p-4 flex items-start justify-between">
                  <div>
                    <p className="font-medium style-text-primary text-sm">{wp.condition}</p>
                    <p className="text-sm style-text-tertiary mt-0.5">Duration: {wp.duration}</p>
                  </div>
                  <span className={`badge-${wp.risk_level}`}>{wp.risk_level}</span>
                </div>
              ))}
            </ClauseSection>
          )}

          {clauses.exclusions?.length > 0 && (
            <ClauseSection title={`Exclusions (${clauses.exclusions.length})`}
              icon={<Shield size={18} className="text-red-500" />}
              isExpanded={expanded["exclusions"]} onToggle={() => toggle("exclusions")}>
              {clauses.exclusions.map((ex, i) => (
                <div key={i} className="p-4 flex items-start justify-between">
                  <div>
                    <p className="font-medium style-text-primary text-sm">{ex.clause}</p>
                    <p className="text-sm style-text-tertiary mt-0.5">{ex.description}</p>
                  </div>
                  <span className={`badge-${ex.risk_level} ml-3 shrink-0`}>{ex.risk_level}</span>
                </div>
              ))}
              <div className="p-3 bg-surface-2 text-xs style-text-tertiary border-t">
                AI may not extract all exclusions from poorly formatted documents. Check your original policy for a complete list.
              </div>
            </ClauseSection>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: "Room Rent Cap", value: clauses.room_rent_cap?.limit || "No cap detected" },
              { label: "Co-payment", value: clauses.co_payment?.percentage || "None detected" },
              { label: "PED Waiting", value: clauses.pre_existing_disease_waiting || "N/A" },
              { label: "Moratorium", value: clauses.moratorium_period || "5 years (IRDAI 2024)" },
              { label: "Network", value: clauses.network_hospitals || "Unknown" },
              { label: "Portability", value: clauses.portability_allowed ? "Allowed" : "Check policy" },
            ].map(({ label, value }) => (
              <div key={label} className="card p-4">
                <p className="text-xs style-text-tertiary mb-1">{label}</p>
                <p className="font-semibold style-text-primary text-sm">{value}</p>
              </div>
            ))}
          </div>

          <div className="text-xs text-center style-text-tertiary pb-2">
            All values above are AI-extracted estimates. Verify against your original policy document.
          </div>
        </div>
      )}

      {/* No clauses extracted yet but doc is loaded */}
      {document && !clauses && (
        <div className="card p-8 text-center">
          <AlertTriangle className="mx-auto text-amber-500 mb-3" size={32} />
          <p className="font-semibold style-text-secondary mb-1">No clauses extracted</p>
          <p className="text-sm style-text-tertiary">
            The AI could not extract structured clauses from this document.
            This can happen with scanned or image-only PDFs.
          </p>
          <button onClick={() => setDocument(null)} className="btn-secondary mt-4 text-sm">
            Try another file
          </button>
        </div>
      )}
    </div>
  );
}

export default function AnalyzerPage() {
  return (
    <Suspense fallback={
      <div className="max-w-4xl flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-violet-400" size={32} />
      </div>
    }>
      <AnalyzerPageInner />
    </Suspense>
  );
}

function ClauseSection({ title, icon, isExpanded, onToggle, children }: {
  title: string; icon: React.ReactNode; isExpanded: boolean; onToggle: () => void; children: React.ReactNode;
}) {
  return (
    <div className="card overflow-hidden">
      <button className="w-full flex items-center justify-between p-5 hover:bg-surface-2 transition" onClick={onToggle}>
        <div className="flex items-center gap-2">{icon}<span className="font-semibold style-text-primary">{title}</span></div>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {isExpanded && <div className="border-t divide-y divide-slate-100">{children}</div>}
    </div>
  );
}