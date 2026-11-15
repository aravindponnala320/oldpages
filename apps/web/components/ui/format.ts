/**
 * Renders a formatted price in its own currency: ₹1,25,000 · $12.50 · CA$45 · £8 · AED 40.
 * Undefined → "Free". Server- and client-safe.
 */
export function formatPrice(
  cents: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (cents == null) return "Free";
  const code = (currency || "INR").toUpperCase();
  const amount = cents / 100;
  try {
    return new Intl.NumberFormat(code === "INR" ? "en-IN" : "en", {
      style: "currency",
      currency: code,
      currencyDisplay: "symbol", // "CA$", "A$", "SGD": a bare "$" is ambiguous across countries
      minimumFractionDigits: Number.isInteger(amount) ? 0 : 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${code} ${amount.toLocaleString()}`; // unknown currency code
  }
}
