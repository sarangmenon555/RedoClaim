"use client";
import { useEffect, useState } from "react";
import { documentsApi } from "@/lib/api";
import Link from "next/link";
import {
  FileText, Upload, Clock, CheckCircle, XCircle,
  Loader2, FileSearch, AlertTriangle, ArrowRight
} from "lucide-react";
import type { Document } from "@/types";
import { format } from "date-fns";

const DOC_TYPE_LABELS: Record<string, string> = {
  policy: "Policy",
  rejection_letter: "Rejection Letter",
  discharge_summary: "Discharge Summary",
  hospital_bill: "Hospital Bill",
  insurer_letter: "Insurer Letter",
  other: "Other",
};

const STATUS_ICON = {
  pending: <Clock size={14} className="text-amber-500" />,
  processing: <Loader2 size={14} className="text-blue-500 animate-spin" />,
  done: <CheckCircle size={14} className="text-green-500" />,
  failed: <XCircle size={14} className="text-red-500" />,
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

useEffect(() => {
  documentsApi.list()
    .then((r) => setDocs(r.data))
    .catch(() => {})
    .finally(() => setLoading(false));

  // Auto-refresh every 5s if any doc is still processing
  const interval = setInterval(() => {
    documentsApi.list().then((r) => {
      setDocs(r.data);
      const stillProcessing = r.data.some(
        (d: Document) => d.ocr_status === "pending" || d.ocr_status === "processing"
      );
      if (!stillProcessing) clearInterval(interval);
    }).catch(() => {});
  }, 5000);

  return () => clearInterval(interval);
}, []);

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in" style={{color:"var(--text-primary)"}}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold style-text-primary">My Documents</h2>
          <p className="style-text-tertiary text-sm mt-1">
            All uploaded insurance documents and their analysis status.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/analyzer" className="btn-primary text-sm">
            <Upload size={14} /> Upload Policy
          </Link>
          <Link href="/dashboard/auditor" className="btn-secondary text-sm">
            <AlertTriangle size={14} /> Upload Rejection
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="card h-20 shimmer" />)}
        </div>
      ) : docs.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="mx-auto style-text-tertiary mb-4" size={48} />
          <p className="font-semibold style-text-secondary mb-2">No documents yet</p>
          <p className="text-sm style-text-tertiary mb-4">
            Upload your insurance policy or rejection letter to get started
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/dashboard/analyzer" className="btn-primary">
              Upload Policy <ArrowRight size={13} />
            </Link>
            <Link href="/dashboard/auditor" className="btn-secondary">
              Upload Rejection
            </Link>
          </div>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-surface-4 bg-surface-2 flex items-center justify-between">
            <p className="text-sm font-medium style-text-secondary">{docs.length} document{docs.length !== 1 ? "s" : ""}</p>
          </div>
          <div className="divide-y divide-slate-100">
            {docs.map((doc) => (
              <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-surface-2 transition">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    doc.doc_type === "policy" ? "bg-surface-2" :
                    doc.doc_type === "rejection_letter" ? "bg-surface-2" : "bg-surface-2"
                  }`}>
                    <FileText size={18} className={
                      doc.doc_type === "policy" ? "text-blue-600" :
                      doc.doc_type === "rejection_letter" ? "text-red-600" : "style-text-tertiary"
                    } />
                  </div>
                  <div>
                    <p className="font-medium style-text-primary text-sm truncate max-w-xs">{doc.file_name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="badge-info text-xs">{DOC_TYPE_LABELS[doc.doc_type]}</span>
                      {doc.insurance_type && (
                        <span className="text-xs style-text-tertiary">{doc.insurance_type}</span>
                      )}
                      <span className="text-xs style-text-tertiary">
                        {doc.created_at ? format(new Date(doc.created_at), "dd MMM yyyy") : ""}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5 text-xs style-text-tertiary">
                    {STATUS_ICON[doc.ocr_status]}
                    <span>{doc.ocr_status === "done" ? "Analyzed" : doc.ocr_status}</span>
                  </div>
                  {doc.doc_type === "policy" && doc.ocr_status === "done" && (
                    <Link
                      href={`/dashboard/analyzer?doc=${doc.id}`}
                      className="btn-secondary text-xs px-2.5 py-1.5"
                    >
                      <FileSearch size={12} /> View
                    </Link>
                  )}
                  {doc.doc_type === "rejection_letter" && doc.ocr_status === "done" && (
                    <Link
                      href={`/dashboard/auditor?doc=${doc.id}`}
                      className="btn-secondary text-xs px-2.5 py-1.5"
                    >
                      <AlertTriangle size={12} /> Audit
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
