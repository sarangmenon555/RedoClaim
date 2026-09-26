"use client";
import { useEffect, useState } from "react";
import { analysisApi, documentsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Calculator, Loader2, Plus, Trash2 } from "lucide-react";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import type { Document } from "@/types";

interface BillItemRow { item: string; amount: string; }

export default function CopayBreakdownPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [totalBill, setTotalBill] = useState("");
  const [roomRent, setRoomRent] = useState("");
  const [daysAdmitted, setDaysAdmitted] = useState("1");
  const [patientAge, setPatientAge] = useState("");
  const [useItemized, setUseItemized] = useState(false);
  const [items, setItems] = useState<BillItemRow[]>([{ item: "", amount: "" }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    documentsApi.list().then((res) =>
      setDocs(res.data.filter((d: Document) => d.doc_type === "policy" && d.ocr_status === "done"))
    ).catch(() => {});
  }, []);

  const addItem = () => setItems([...items, { item: "", amount: "" }]);
  const removeItem = (i: number) => setItems(items.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: keyof BillItemRow, value: string) =>
    setItems(items.map((row, idx) => (idx === i ? { ...row, [field]: value } : row)));

  const runCalc = async () => {
    if (!documentId || !totalBill || !roomRent) {
      toast.error("Fill in the policy, total bill, and room rent.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const billItems = useItemized
        ? items.filter((r) => r.item.trim() && r.amount).map((r) => ({ item: r.item, amount: parseFloat(r.amount) }))
        : undefined;

      const res = await analysisApi.copayBreakdown({
        document_id: documentId,
        total_bill_amount: parseFloat(totalBill),
        actual_room_rent_per_day: parseFloat(roomRent),
        days_admitted: parseInt(daysAdmitted) || 1,
        bill_items: billItems,
        patient_age: patientAge ? parseInt(patientAge) : undefined,
      });
      setResult(res.data);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not calculate the breakdown.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <Calculator size={22} style={{ color: "#A78BFA" }} /> Co-pay / Deductible Breakdown
        </h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
          Plan before you claim — enter your actual hospital bill and room rent to see precisely what
          the insurer is likely to pay, including the exact proportionate room-rent deduction.
        </p>
      </div>

      <DisclaimerBanner variant="inline" />

      <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
        <div>
          <label className="label">Policy document</label>
          <select className="input" value={documentId} onChange={(e) => setDocumentId(e.target.value)} suppressHydrationWarning>
            <option value="">Select a policy...</option>
            {docs.map((d) => <option key={d.id} value={d.id}>{d.file_name}</option>)}
          </select>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="label">Total bill (₹)</label>
            <input type="number" className="input" value={totalBill} onChange={(e) => setTotalBill(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">Room rent/day (₹)</label>
            <input type="number" className="input" value={roomRent} onChange={(e) => setRoomRent(e.target.value)} suppressHydrationWarning />
          </div>
          <div>
            <label className="label">Days admitted</label>
            <input type="number" className="input" value={daysAdmitted} onChange={(e) => setDaysAdmitted(e.target.value)} suppressHydrationWarning />
          </div>
        </div>

        <div>
          <label className="label">Patient age (optional — for co-payment rules)</label>
          <input type="number" className="input w-32" value={patientAge} onChange={(e) => setPatientAge(e.target.value)} suppressHydrationWarning />
        </div>

        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-secondary)" }}>
          <input type="checkbox" checked={useItemized} onChange={(e) => setUseItemized(e.target.checked)} suppressHydrationWarning />
          Break down by itemized bill (surgeon fees, medicines, etc.)
        </label>

        {useItemized && (
          <div className="space-y-2">
            {items.map((row, i) => (
              <div key={i} className="flex gap-2">
                <input className="input flex-1" placeholder="Item (e.g. Surgeon fees)" value={row.item}
                  onChange={(e) => updateItem(i, "item", e.target.value)} suppressHydrationWarning />
                <input type="number" className="input w-32" placeholder="Amount" value={row.amount}
                  onChange={(e) => updateItem(i, "amount", e.target.value)} suppressHydrationWarning />
                <button onClick={() => removeItem(i)} className="btn-secondary px-3" suppressHydrationWarning><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={addItem} className="btn-secondary text-xs px-3 py-1.5 inline-flex items-center gap-1" suppressHydrationWarning>
              <Plus size={12} /> Add item
            </button>
          </div>
        )}

        <button onClick={runCalc} disabled={loading} className="btn-primary w-full justify-center py-3" suppressHydrationWarning>
          {loading ? <><Loader2 size={16} className="animate-spin" /> Calculating...</> : "Calculate breakdown"}
        </button>
      </div>

      {result && (
        <div className="card p-6 space-y-4" style={{ background: "var(--surface-1)", border: "1px solid var(--surface-5)" }}>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl p-4 text-center" style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Insurer should pay</p>
              <p className="text-xl font-bold" style={{ color: "#4ADE80" }}>₹{result.estimated_insurer_payout.toLocaleString("en-IN")}</p>
            </div>
            <div className="rounded-xl p-4 text-center" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Your out-of-pocket</p>
              <p className="text-xl font-bold" style={{ color: "#F87171" }}>₹{result.your_out_of_pocket.toLocaleString("en-IN")}</p>
            </div>
          </div>

          {result.deductions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold" style={{ color: "var(--text-tertiary)" }}>Deductions applied</p>
              {result.deductions.map((d: any, i: number) => (
                <div key={i} className="rounded-lg p-3" style={{ background: "var(--surface-2)", border: "1px solid var(--surface-5)" }}>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: "var(--text-secondary)" }}>{d.reason}</span>
                    <span className="font-semibold" style={{ color: "#F87171" }}>-₹{d.amount.toLocaleString("en-IN")}</span>
                  </div>
                  {d.line_items && (
                    <div className="mt-2 space-y-1">
                      {d.line_items.map((li: any, j: number) => (
                        <div key={j} className="flex justify-between text-xs" style={{ color: "var(--text-tertiary)" }}>
                          <span>{li.item}</span>
                          <span>₹{li.billed.toLocaleString("en-IN")} → ₹{li.eligible.toLocaleString("en-IN")}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {result.notes.length > 0 && (
            <ul className="space-y-1.5">
              {result.notes.map((n: string, i: number) => (
                <li key={i} className="text-xs" style={{ color: "var(--text-secondary)" }}>• {n}</li>
              ))}
            </ul>
          )}

          <p className="text-xs pt-2" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-5)" }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
