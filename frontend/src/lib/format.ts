/**
 * Consistent INR currency formatting across the app. Use formatINR for a
 * plain rupee figure, formatINRCompact for the "₹X.XL / ₹X.XCr" short form
 * used in list views and cards where space is tight.
 */
export function formatINR(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  return `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function formatINRCompact(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)}Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(1)}L`;
  return formatINR(amount);
}
