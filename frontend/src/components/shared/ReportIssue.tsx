"use client";
import { useState } from "react";
import { usePathname } from "next/navigation";
import toast from "react-hot-toast";
import { feedbackApi } from "@/lib/api";
import { useLanguageStore } from "@/store/language";

const CATEGORIES = [
  { value: "incorrect_information", label: "Incorrect Information" },
  { value: "incorrect_source", label: "Incorrect Source" },
  { value: "document_misunderstood", label: "Document Misunderstood" },
  { value: "missing_information", label: "Missing Information" },
  { value: "language_translation", label: "Language Or Translation Issue" },
  { value: "other", label: "Other" },
];

const ANSWER_ROUTES = [
  "/dashboard/analyzer",
  "/dashboard/cis",
  "/dashboard/auditor",
  "/dashboard/ask",
  "/dashboard/estimator",
  "/dashboard/waiting-period",
  "/dashboard/compare-policies",
  "/dashboard/explain",
  "/dashboard/copay-breakdown",
  "/dashboard/renewal-check",
  "/dashboard/settlement-audit",
  "/dashboard/preauth-check",
  "/dashboard/hospital-verify",
  "/dashboard/appeals",
  "/dashboard/portability",
  "/dashboard/e-jagriti",
  "/dashboard/ncb-check",
  "/dashboard/sum-insured-check",
  "/dashboard/claims",
];

export default function ReportIssue() {
  const pathname = usePathname();
  const language = useLanguageStore((s) => s.language);
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState("");
  const [details, setDetails] = useState("");
  const [sending, setSending] = useState(false);

  const visible = ANSWER_ROUTES.some((r) => pathname === r || pathname.startsWith(`${r}/`));
  if (!visible) return null;

  const close = () => {
    setOpen(false);
    setCategory("");
    setDetails("");
  };

  const submit = async () => {
    if (!category) {
      toast.error("Please choose the type of issue.");
      return;
    }
    setSending(true);
    try {
      await feedbackApi.reportIssue({
        category,
        details: details.trim() || undefined,
        page_path: pathname,
        language,
      });
      toast.success("Thank you. Your report has been recorded.");
      close();
    } catch {
      toast.error("Could not send your report. Please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 text-xs px-3 py-2 rounded-lg font-medium transition-all"
        style={{
          background: "var(--surface-2)",
          color: "var(--text-secondary)",
          border: "1px solid var(--surface-5)",
        }}
      >
        Report An Issue With This Answer
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          style={{ background: "rgba(0,0,0,0.6)" }}
          onClick={close}
        >
          <div
            className="card p-6 w-full max-w-md space-y-4"
            style={{ background: "var(--surface-1)" }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-issue-title"
          >
            <div>
              <h2 id="report-issue-title" className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Report An Issue With This Answer
              </h2>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
                Your report helps improve RedoClaim. Please do not include personal, policy or health details.
              </p>
            </div>

            <div className="space-y-2">
              {CATEGORIES.map((c) => (
                <label
                  key={c.value}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm cursor-pointer"
                  style={{
                    background: category === c.value ? "rgba(139,92,246,0.15)" : "var(--surface-2)",
                    border: `1px solid ${category === c.value ? "rgba(139,92,246,0.35)" : "var(--surface-4)"}`,
                    color: "var(--text-primary)",
                  }}
                >
                  <input
                    type="radio"
                    name="issue-category"
                    value={c.value}
                    checked={category === c.value}
                    onChange={() => setCategory(c.value)}
                  />
                  {c.label}
                </label>
              ))}
            </div>

            <textarea
              className="input w-full text-sm"
              rows={3}
              maxLength={1000}
              placeholder="Add details (optional)"
              value={details}
              onChange={(e) => setDetails(e.target.value)}
            />

            <div className="flex justify-end gap-2">
              <button onClick={close} className="btn-ghost text-sm" disabled={sending}>
                Cancel
              </button>
              <button onClick={submit} className="btn-primary text-sm" disabled={sending || !category}>
                {sending ? "Sending..." : "Submit Report"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
