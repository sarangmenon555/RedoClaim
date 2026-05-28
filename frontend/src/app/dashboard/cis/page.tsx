"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { documentsApi, analysisApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Upload, Loader2, CheckCircle, AlertTriangle, Info, Shield } from "lucide-react";

export default function CISPage() {
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [docId, setDocId] = useState("");
  const [result, setResult] = useState<any>(null);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0]; if (!file) return;
    setUploading(true);
    try {
      const res = await documentsApi.upload(file, "other");
      const id = res.data.document_id;
      toast.success("CIS uploaded. Processing...");
      const interval = setInterval(async () => {
        const docRes = await documentsApi.get(id);
        if (docRes.data.ocr_status === "done") {
          setDocId(id); clearInterval(interval);
          toast.success("CIS ready to scan!");
        }
      }, 3000);
      setTimeout(() => clearInterval(interval), 120000);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Upload failed");
    } finally { setUploading(false); }
  }, []);

  const scanCIS = async () => {
    if (!docId) return;
    setScanning(true);
    try {
      const res = await analysisApi.scanCIS(docId);
      setResult(res.data);
      toast.success("CIS scanned successfully!");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Scan failed");
    } finally { setScanning(false); }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "application/pdf": [], "image/*": [] }, multiple: false, disabled: uploading });

  const cis = result?.cis_analysis;

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">CIS Scanner</h2>
        <p className="style-text-tertiary text-sm mt-1">
          Scan your Customer Information Sheet (CIS). IRDAI Master Circular 2024, Para 4.2:
          insurer cannot enforce exclusions not listed in your CIS.
        </p>
      </div>

      <div className="card p-4 bg-surface-2 border-amber-500\/20 flex items-start gap-3">
        <Info className="text-amber-600 shrink-0" size={17} />
        <div>
          <p className="font-semibold text-amber-800 text-sm">What is a CIS?</p>
          <p className="text-sm text-amber-700 mt-0.5">
            Every insurer must provide a Customer Information Sheet at policy issuance summarising
            all inclusions and exclusions. If yours wasn't provided, that itself is a violation.
            Upload it here to extract exactly what is and isn't covered.
          </p>
        </div>
      </div>

      {!docId && (
        <div {...getRootProps()} className={`card border-2 border-dashed p-10 text-center cursor-pointer transition-all ${isDragActive ? "border-violet-400 bg-surface-2" : "border-surface-5 hover:border-violet-400"}`}>
          <input {...getInputProps()} />
          {uploading ? (
            <div className="flex flex-col items-center gap-3"><Loader2 className="animate-spin text-violet-400" size={32} /><p className="font-medium style-text-secondary">Processing CIS...</p></div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 bg-surface-2 rounded-xl flex items-center justify-center"><Upload className="text-violet-400" size={24} /></div>
              <p className="font-semibold style-text-primary">Upload your Customer Information Sheet</p>
              <p className="text-sm style-text-tertiary">PDF or image</p>
            </div>
          )}
        </div>
      )}

      {docId && !result && (
        <div className="card p-5 text-center space-y-4">
          <CheckCircle className="text-green-500 mx-auto" size={32} />
          <p className="font-medium style-text-primary">CIS uploaded and ready</p>
          <button onClick={scanCIS} disabled={scanning} className="btn-primary">
            {scanning ? <><Loader2 size={15} className="animate-spin" /> Scanning CIS with AI...</> : <>Scan CIS — Extract Inclusions & Exclusions</>}
          </button>
        </div>
      )}

      {cis && (
        <div className="space-y-4 animate-slide-up">
          <div className="card p-5 border-l-4 border-green-500">
            <p className="font-semibold style-text-primary">{cis.insurer_name} — {cis.policy_name}</p>
            <p className="text-sm style-text-tertiary">Sum Insured: {cis.sum_insured}</p>
          </div>

          {/* Plain English Summary */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="card p-5 border-l-4 border-green-400">
              <div className="flex items-center gap-2 mb-2"><CheckCircle size={15} className="text-green-600" /><p className="font-semibold style-text-primary">What IS covered</p></div>
              <p className="text-sm style-text-secondary leading-relaxed">{cis.plain_english_inclusions}</p>
            </div>
            <div className="card p-5 border-l-4 border-red-400">
              <div className="flex items-center gap-2 mb-2"><AlertTriangle size={15} className="text-red-600" /><p className="font-semibold style-text-primary">What is NOT covered</p></div>
              <p className="text-sm style-text-secondary leading-relaxed">{cis.plain_english_exclusions}</p>
            </div>
          </div>

          {/* Risky exclusions */}
          {cis.risky_exclusions?.length > 0 && (
            <div className="card overflow-hidden">
              <div className="p-4 bg-surface-2 border-b border-red-500\/20 flex items-center gap-2">
                <Shield size={15} className="text-red-600" />
                <span className="font-semibold text-red-800 text-sm">Potentially questionable exclusions</span>
              </div>
              <div className="divide-y divide-slate-100">
                {cis.risky_exclusions.map((r: any, i: number) => (
                  <div key={i} className="p-4">
                    <p className="font-medium style-text-primary text-sm">{r.exclusion}</p>
                    <p className="text-xs text-red-600 mt-1">{r.risk}</p>
                    {r.irdai_note && <p className="text-xs style-text-tertiary mt-1">📋 {r.irdai_note}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Full inclusions list */}
          {cis.inclusions?.length > 0 && (
            <div className="card p-5">
              <p className="font-semibold style-text-primary mb-3">All Inclusions ({cis.inclusions.length})</p>
              <div className="space-y-2">
                {cis.inclusions.map((inc: any, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle size={13} className="text-green-500 mt-0.5 shrink-0" />
                    <div><span className="font-medium style-text-secondary">{inc.benefit}</span>{inc.coverage_limit && <span className="style-text-tertiary"> — {inc.coverage_limit}</span>}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card p-4 bg-surface-2 border-neon-500\/20">
            <p className="text-xs text-green-800"><strong>IRDAI Note:</strong> {result.irdai_note}</p>
          </div>
        </div>
      )}
    </div>
  );
}
