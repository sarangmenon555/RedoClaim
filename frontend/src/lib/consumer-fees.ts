export const LAKH = 100000;
export const CRORE = 10000000;

export const FEE_SLABS: { upTo: number; fee: number }[] = [
  { upTo: 5 * LAKH, fee: 0 },
  { upTo: 10 * LAKH, fee: 200 },
  { upTo: 20 * LAKH, fee: 400 },
  { upTo: 50 * LAKH, fee: 1000 },
  { upTo: 1 * CRORE, fee: 2000 },
  { upTo: 2 * CRORE, fee: 2500 },
  { upTo: 4 * CRORE, fee: 3000 },
  { upTo: 6 * CRORE, fee: 4000 },
  { upTo: 8 * CRORE, fee: 5000 },
  { upTo: 10 * CRORE, fee: 6000 },
];

export const TOP_FEE = 7500;

export type ConsumerForum = "district" | "state" | "national";

export function formatRupees(value: number): string {
  return "\u20b9" + Math.round(value).toLocaleString("en-IN");
}

export function formatLimit(value: number): string {
  return value % CRORE === 0 ? `\u20b9${value / CRORE} crore` : `\u20b9${value / LAKH} lakh`;
}

export function consumerFee(consideration: number): number {
  for (const slab of FEE_SLABS) {
    if (consideration <= slab.upTo) return slab.fee;
  }
  return TOP_FEE;
}

export function consumerForum(consideration: number): ConsumerForum {
  if (consideration <= 50 * LAKH) return "district";
  if (consideration <= 2 * CRORE) return "state";
  return "national";
}

export function slabLabel(index: number): string {
  if (index >= FEE_SLABS.length) return `Above ${formatLimit(FEE_SLABS[FEE_SLABS.length - 1].upTo)}`;
  const upper = FEE_SLABS[index].upTo;
  if (index === 0) return `Up to ${formatLimit(upper)}`;
  return `Above ${formatLimit(FEE_SLABS[index - 1].upTo)} up to ${formatLimit(upper)}`;
}
