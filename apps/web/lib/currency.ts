// Which currency a listing is priced in, from the country the book is in.
// Keep in sync with apps/api/src/oldpages_api/geo/currency.py (the API decides; this
// only lets the Sell form show the right symbol before the listing exists).

const EURO =
  "AT BE CY DE EE ES FI FR GR HR IE IT LT LU LV MT NL PT SI SK".split(" ");

const CURRENCY_BY_COUNTRY: Record<string, string> = {
  ...Object.fromEntries(EURO.map((code) => [code, "EUR"])),
  IN: "INR",
  AE: "AED",
  AU: "AUD",
  BD: "BDT",
  BH: "BHD",
  BR: "BRL",
  CA: "CAD",
  CH: "CHF",
  CN: "CNY",
  DK: "DKK",
  EG: "EGP",
  GB: "GBP",
  HK: "HKD",
  ID: "IDR",
  IL: "ILS",
  JP: "JPY",
  KE: "KES",
  KR: "KRW",
  KW: "KWD",
  LK: "LKR",
  MV: "MVR",
  MX: "MXN",
  MY: "MYR",
  NG: "NGN",
  NO: "NOK",
  NP: "NPR",
  NZ: "NZD",
  OM: "OMR",
  PH: "PHP",
  PK: "PKR",
  PL: "PLN",
  QA: "QAR",
  SA: "SAR",
  SE: "SEK",
  SG: "SGD",
  TH: "THB",
  TR: "TRY",
  TW: "TWD",
  US: "USD",
  VN: "VND",
  ZA: "ZAR",
};

export function currencyForCountry(
  countryCode: string | null | undefined,
): string {
  const code = (countryCode ?? "IN").toUpperCase();
  return CURRENCY_BY_COUNTRY[code === "INDIA" ? "IN" : code] ?? "USD";
}

/** "₹", "$", "CA$", "£", "AED"… as the reader's browser would print it. */
export function currencySymbol(currency: string): string {
  try {
    const part = new Intl.NumberFormat(currency === "INR" ? "en-IN" : "en", {
      style: "currency",
      currency,
      currencyDisplay: "symbol", // "CA$", "A$", "SGD": a bare "$" is ambiguous across countries
    })
      .formatToParts(0)
      .find((p) => p.type === "currency");
    return part?.value ?? currency;
  } catch {
    return currency;
  }
}

/** Left padding for an input with the currency symbol drawn inside it. */
export function symbolPadding(currency: string): string {
  return `calc(1.25rem + ${currencySymbol(currency).length}ch)`;
}
