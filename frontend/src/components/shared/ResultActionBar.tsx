"use client";
import { useState } from "react";
import toast from "react-hot-toast";
import { Mail, Printer, Check } from "lucide-react";

interface Props {
  /** Plain-text body, formatted the way you'd want it to read in an email. */
  emailBody: string;
  /** Optional subject line — appended as a mailto: hint if the person clicks through. */
  subject?: string;
  /** id of the DOM element to print — should contain only the result content. */
  printTargetId?: string;
  className?: string;
}

/**
 * Drop this under any analysis result to get "Copy as email" and
 * "Export as PDF" for free. PDF export uses the browser's native
 * print-to-PDF (via a print-only stylesheet targeting printTargetId)
 * rather than a server-side renderer — zero backend cost, works
 * identically for every tool's output without a dedicated endpoint per tool.
 * The full claim Audit Trail keeps its dedicated ReportLab PDF (richer,
 * multi-section document) — this is for single-result tool outputs.
 */
export function ResultActionBar({ emailBody, subject, printTargetId, className }: Props) {
  const [copied, setCopied] = useState(false);

  const copyAsEmail = async () => {
    try {
      await navigator.clipboard.writeText(emailBody);
      setCopied(true);
      toast.success("Copied — paste into your email or message.");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Couldn't copy. Try selecting the text manually.");
    }
  };

  const exportAsPdf = () => {
    const target = printTargetId ? document.getElementById(printTargetId) : null;
    if (!target) {
      toast.error("Nothing to export yet.");
      return;
    }
    const printWindow = window.open("", "_blank", "width=800,height=900");
    if (!printWindow) {
      toast.error("Please allow pop-ups to export as PDF.");
      return;
    }
    printWindow.document.write(`
      <html>
        <head>
          <title>${subject || "RedoClaim Export"}</title>
          <style>
            body { font-family: Georgia, 'Times New Roman', serif; color: #111; padding: 32px; line-height: 1.6; max-width: 700px; margin: 0 auto; }
            h1, h2, h3 { color: #4F46E5; }
            table { width: 100%; border-collapse: collapse; margin: 12px 0; }
            td, th { border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 13px; }
            .muted { color: #666; font-size: 12px; }
          </style>
        </head>
        <body>${target.innerHTML}</body>
      </html>
    `);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  return (
    <div className={`flex gap-2 ${className || ""}`}>
      <button onClick={copyAsEmail} className="btn-secondary text-xs px-3 py-1.5 inline-flex items-center gap-1.5" suppressHydrationWarning>
        {copied ? <Check size={12} /> : <Mail size={12} />}
        {copied ? "Copied" : "Copy as email"}
      </button>
      {printTargetId && (
        <button onClick={exportAsPdf} className="btn-secondary text-xs px-3 py-1.5 inline-flex items-center gap-1.5" suppressHydrationWarning>
          <Printer size={12} /> Export as PDF
        </button>
      )}
    </div>
  );
}
