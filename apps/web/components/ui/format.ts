/**
 * Renders a formatted price. Undefined → "Free". Server- and client-safe.
 */
export function formatPrice(cents: number | null | undefined, currency: string): string {
  if (cents == null) return "Free";
  const amount = cents / 100;
  if (currency === "INR") return `₹${amount.toLocaleString("en-IN")}`;
  return `${currency} ${amount.toLocaleString()}`;
}
