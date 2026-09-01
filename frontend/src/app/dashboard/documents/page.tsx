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
import { useT } from "@/lib/i18n/useT";

const DOC_TYPE_KEYS: Record<string, string> = {
  policy: "doc_type_policy",
  rejection_letter: "doc_type_rejection",
  discharge_summary: "doc_type_discharge",
  hospital_bill: "doc_type_bill",
  insurer_letter: "doc_type_insurer",
  // Motor
  survey_report: "doc_type_survey",
  rc_book: "doc_type_rc",
  driving_licence: "doc_type_dl",
  fir: "doc_type_fir",
  repair_estimate: "doc_type_estimate",
  // Life
  death_certificate: "doc_type_death",
  nominee_id: "doc_type_nominee",
  medical_report: "doc_type_medical",
  other: "doc_type_other",
};

const STATUS_ICON = {
  pending: <Clock size={14} className="text-amber-500" />,
  processing: <Loader2 size={14} className="text-blue-500 animate-spin" />,
  done: <CheckCircle size={14} className="text-green-500" />,
  failed: <XCircle size={14} className="text-red-500" />,
};

export default function DocumentsPage() {
  const t = useT();
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
          <h2 className="text-2xl font-bold style-text-primary">{t("doc_title")}</h2>
          <p className="style-text-tertiary text-sm mt-1">
            {t("doc_subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/analyzer" className="btn-primary text-sm">
            <Upload size={14} /> {t("doc_upload_policy")}
          </Link>
          <Link href="/dashboard/auditor" className="btn-secondary text-sm">
            <AlertTriangle size={14} /> {t("doc_upload_rejection")}
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
          <p className="font-semibold style-text-secondary mb-2">{t("doc_empty_title")}</p>
          <p className="text-sm style-text-tertiary mb-4">
            {t("doc_empty_desc")}
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/dashboard/analyzer" className="btn-primary">
              {t("doc_upload_policy")} <ArrowRight size={13} />
            </Link>
            <Link href="/dashboard/auditor" className="btn-secondary">
              {t("doc_upload_rejection")}
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
                      <span className="badge-info text-xs">{doc.doc_type in DOC_TYPE_KEYS ? t(DOC_TYPE_KEYS[doc.doc_type]) : doc.doc_type}</span>
                      {doc.insurance_type && (
                        <span className="text-xs style-text-tertiary capitalize">{doc.insurance_type}</span>
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
                    <span>{doc.ocr_status === "done" ? t("doc_analyzed") : doc.ocr_status}</span>
                  </div>
                  {doc.doc_type === "policy" && doc.ocr_status === "done" && (
                    <Link
                      href={`/dashboard/analyzer?doc=${doc.id}`}
                      className="btn-secondary text-xs px-2.5 py-1.5"
                    >
                      <FileSearch size={12} /> {t("doc_view")}
                    </Link>
                  )}
                  {doc.doc_type === "rejection_letter" && doc.ocr_status === "done" && (
                    <Link
                      href={`/dashboard/auditor?doc=${doc.id}`}
                      className="btn-secondary text-xs px-2.5 py-1.5"
                    >
                      <AlertTriangle size={12} /> {t("doc_audit")}
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
