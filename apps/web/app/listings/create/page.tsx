"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getAccessToken } from "../../../lib/auth";
import { Container, PageHeader } from "../../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Intent = "sell" | "exchange" | "give_away" | "lend_rent" | "request";
type Condition = "new_sealed" | "like_new" | "excellent" | "very_good" | "good" | "acceptable" | "poor";
type Scope = "personal" | "business" | "institution";
type Visibility = "public" | "private" | "business_only" | "institution_only";

interface BusinessProfile { id: string; name: string; status: string; }
interface Institution { id: string; name: string; type: string; status: string; }

interface BookResult {
  id: string;
  title: string;
  authors: string[];
  isbn_13?: string;
  publication_year?: number;
}

const INTENT_OPTIONS: { key: Intent; icon: string; title: string; subtitle: string; color: string }[] = [
  { key: "sell",      icon: "💰", title: "Sell it",           subtitle: "Get money for your book permanently",      color: "#2563eb" },
  { key: "exchange",  icon: "🔄", title: "Exchange it",       subtitle: "Swap for a book you need",                 color: "#2563eb" },
  { key: "give_away", icon: "🎁", title: "Give it away",      subtitle: "Donate it free to a fellow reader",        color: "#9333ea" },
  { key: "lend_rent", icon: "📤", title: "Lend / Rent it",    subtitle: "Share temporarily, get your book back",    color: "#d97706" },
  { key: "request",   icon: "🔍", title: "Request a book",    subtitle: "Looking for someone who has this book",    color: "#dc2626" },
];

const CONDITIONS: { key: Condition; label: string; desc: string; color: string }[] = [
  { key: "new_sealed",  label: "New / Sealed",  desc: "Unopened, mint condition",          color: "#065f46" },
  { key: "like_new",    label: "Like New",       desc: "Read once, no marks",               color: "#047857" },
  { key: "excellent",   label: "Excellent",      desc: "Minor wear, no markings",           color: "#0369a1" },
  { key: "very_good",   label: "Very Good",      desc: "Some wear, very minor marks",       color: "#1d4ed8" },
  { key: "good",        label: "Good",           desc: "Normal wear, may have highlights",  color: "#92400e" },
  { key: "acceptable",  label: "Acceptable",     desc: "Heavy wear but fully readable",     color: "#b45309" },
  { key: "poor",        label: "Poor",           desc: "Heavily worn, readable",            color: "#991b1b" },
];

const STEPS = ["Intent", "Book", "Details", "Scope", "Location", "Review"];

function StepProgress({ current }: { current: number }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 0, marginBottom: "2rem" }}>
      {STEPS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={label} style={{ display: "flex", alignItems: "flex-start", flex: i < STEPS.length - 1 ? 1 : "none" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.25rem" }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: done ? "#2563eb" : active ? "#fff" : "#f3f4f6",
                border: `2px solid ${active || done ? "#2563eb" : "#e5e7eb"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "0.8rem", fontWeight: 700,
                color: done ? "white" : active ? "#2563eb" : "#9ca3af",
                transition: "all 0.2s", flexShrink: 0,
              }}>
                {done ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: "0.7rem", fontWeight: active ? 600 : 400, color: active ? "#2563eb" : done ? "#374151" : "#9ca3af", whiteSpace: "nowrap" }}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{ flex: 1, height: 2, background: done ? "#2563eb" : "#e5e7eb", margin: "0.9rem 0.375rem 0", transition: "background 0.2s" }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function VisibilityOption({ value, current, onChange, icon, title, desc, color }: { value: Visibility; current: Visibility; onChange: (v: Visibility) => void; icon: string; title: string; desc: string; color: string }) {
  const active = current === value;
  return (
    <button onClick={() => onChange(value)} style={{ display: "flex", alignItems: "center", gap: "0.875rem", padding: "0.875rem 1rem", border: `1.5px solid ${active ? color : "#e5e7eb"}`, borderRadius: 8, background: active ? `${color}08` : "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.15s" }}>
      <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <p style={{ fontWeight: 600, color: "#1f2933", margin: 0, fontSize: "0.875rem" }}>{title}</p>
        <p style={{ color: "#6b7280", margin: 0, fontSize: "0.78rem" }}>{desc}</p>
      </div>
      <div style={{ width: 18, height: 18, borderRadius: "50%", border: `2px solid ${active ? color : "#d1d5db"}`, background: active ? color : "transparent", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        {active && <div style={{ width: 6, height: 6, borderRadius: "50%", background: "white" }} />}
      </div>
    </button>
  );
}

const labelStyle: React.CSSProperties = { fontSize: "0.8rem", fontWeight: 600, color: "#374151", letterSpacing: "0.01em" };
const inputStyle: React.CSSProperties = {
  width: "100%", padding: "0.7rem 0.875rem", boxSizing: "border-box",
  border: "1.5px solid #e5e7eb", borderRadius: 8, fontSize: "0.9rem",
  background: "#fff", color: "#1f2933", outline: "none", transition: "border-color 0.15s",
};

export default function CreateListingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [intent, setIntent] = useState<Intent | null>(null);

  // Scope & visibility
  const [scope, setScope] = useState<Scope>("personal");
  const [visibility, setVisibility] = useState<Visibility>("public");
  const [myBusiness, setMyBusiness] = useState<BusinessProfile | null>(null);
  const [myInstitution, setMyInstitution] = useState<Institution | null>(null);
  const [scopeLoading, setScopeLoading] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    setScopeLoading(true);
    Promise.all([
      fetch(`${API_BASE}/api/v1/business/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API_BASE}/api/v1/institutions?limit=1`, { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => r.ok ? r.json() : null).catch(() => null),
    ]).then(([biz, inst]) => {
      if (biz?.id && biz.status === "active") setMyBusiness(biz);
      const instItems = inst?.items ?? [];
      const activeInst = instItems.find((i: Institution) => i.status === "active");
      if (activeInst) setMyInstitution(activeInst);
    }).finally(() => setScopeLoading(false));
  }, []);

  const [bookQuery, setBookQuery] = useState("");
  const [bookResults, setBookResults] = useState<BookResult[]>([]);
  const [bookSearching, setBookSearching] = useState(false);
  const [selectedBook, setSelectedBook] = useState<BookResult | null>(null);
  const [manualIsbn, setManualIsbn] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [manualAuthor, setManualAuthor] = useState("");
  const [price, setPrice] = useState("");
  const [negotiable, setNegotiable] = useState(true);
  const [openToExchange, setOpenToExchange] = useState(false);
  const [exchangePrefs, setExchangePrefs] = useState("");
  const [description, setDescription] = useState("");
  const [condition, setCondition] = useState<Condition | null>(null);
  const [lendingDays, setLendingDays] = useState("14");
  const [chargeRent, setChargeRent] = useState(false);
  const [rentPerDay, setRentPerDay] = useState("");
  const [deposit, setDeposit] = useState("");
  const [conditionFlags, setConditionFlags] = useState({ handwritten_notes: false, torn_pages: false, water_damage: false, stains: false, missing_pages: false, loose_binding: false });
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [campusPickup, setCampusPickup] = useState(true);
  const [offersShipping, setOffersShipping] = useState(false);

  const isRequest = intent === "request";
  const isFree = intent === "give_away" || intent === "exchange";
  const selectedIntentOpt = INTENT_OPTIONS.find((o) => o.key === intent);

  const canContinue = [
    !!intent,
    !!(selectedBook || manualIsbn.trim() || manualTitle.trim() || bookQuery.trim()),
    !!(isRequest || condition),
    true, // scope step always valid
    !!city.trim(),
    true,
  ][step];

  async function searchBooks(q: string) {
    if (q.trim().length < 2) { setBookResults([]); return; }
    setBookSearching(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/books?q=${encodeURIComponent(q)}&limit=8`, {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      if (res.ok) { const d = await res.json(); setBookResults(d.items ?? []); }
    } catch { /* ignore */ } finally { setBookSearching(false); }
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    const modes = intent === "sell" ? ["sell"] : intent === "exchange" ? ["exchange"] : intent === "give_away" ? ["donate"] : intent === "lend_rent" ? [chargeRent ? "rent" : "lend"] : ["request"];
    const body: Record<string, unknown> = {
      listing_modes: modes,
      scope,
      visibility,
      business_profile_id: scope === "business" && myBusiness ? myBusiness.id : undefined,
      institution_id: scope === "institution" && myInstitution ? myInstitution.id : undefined,
      description: description || undefined,
      price_amount_cents: (intent === "sell" && price) ? Math.round(parseFloat(price) * 100) : (intent === "lend_rent" && chargeRent && rentPerDay) ? Math.round(parseFloat(rentPerDay) * 100) : null,
      negotiable,
      open_to_exchange: openToExchange,
      exchange_preferences: (openToExchange || intent === "exchange") && exchangePrefs ? exchangePrefs : undefined,
      lending_duration_days: intent === "lend_rent" ? (parseInt(lendingDays) || 14) : undefined,
      rental_fee_per_day_cents: intent === "lend_rent" && chargeRent && rentPerDay ? Math.round(parseFloat(rentPerDay) * 100) : undefined,
      rental_deposit_amount_cents: intent === "lend_rent" && deposit ? Math.round(parseFloat(deposit) * 100) : undefined,
      condition: isRequest ? undefined : { condition, ...conditionFlags },
      location: { city, state: state || undefined, neighborhood: neighborhood || undefined, public_area: [neighborhood, city, state].filter(Boolean).join(", "), country: "IN", campus_pickup: campusPickup },
      delivery_methods: [{ method: "pickup", enabled: campusPickup }, { method: "shipping", enabled: offersShipping }].filter((d) => d.enabled),
    };
    if (selectedBook) {
      body.book_id = selectedBook.id;
    } else if (manualIsbn.trim()) {
      body.isbn = manualIsbn.trim();
      body.book_title = manualTitle.trim() || bookQuery.trim() || undefined;
      body.book_author = manualAuthor.trim() || undefined;
    } else {
      body.book_title = manualTitle.trim() || bookQuery.trim();
      body.book_author = manualAuthor.trim() || undefined;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/listings`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${getAccessToken()}` }, body: JSON.stringify(body) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? data.invalid_params?.[0]?.msg ?? "Failed to create listing");
      const publishRes = await fetch(`${API_BASE}/api/v1/listings/${data.id}/publish`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      });
      if (!publishRes.ok) {
        const pd = await publishRes.json().catch(() => ({}));
        throw new Error(pd.detail ?? "Listing created but could not be published. Go to My Listings to publish it.");
      }
      router.push(`/listings/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={720}>
        <PageHeader
          eyebrow="Sell"
          title="Post a Listing"
          subtitle="Reach readers near you in minutes — it's free."
        />

        <StepProgress current={step} />

        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "2rem" }}>

          {/* Step 0 — Intent */}
          {step === 0 && (
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.375rem" }}>What do you want to do with this book?</h2>
              <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1.5rem" }}>Choose the option that best describes your intent</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {INTENT_OPTIONS.map((opt) => (
                  <button key={opt.key} onClick={() => setIntent(opt.key)} style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1rem 1.25rem", border: `2px solid ${intent === opt.key ? opt.color : "#e5e7eb"}`, borderRadius: 10, background: intent === opt.key ? `${opt.color}10` : "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.15s" }}>
                    <div style={{ width: 44, height: 44, borderRadius: 10, background: intent === opt.key ? opt.color : "#f9fafb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", flexShrink: 0, transition: "background 0.15s" }}>{opt.icon}</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 700, color: "#1f2933", margin: 0, fontSize: "0.95rem" }}>{opt.title}</p>
                      <p style={{ color: "#6b7280", margin: 0, fontSize: "0.825rem" }}>{opt.subtitle}</p>
                    </div>
                    {intent === opt.key && <div style={{ width: 22, height: 22, borderRadius: "50%", background: opt.color, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><span style={{ color: "white", fontSize: "0.7rem", fontWeight: 800 }}>✓</span></div>}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 1 — Book */}
          {step === 1 && (
            <div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.375rem" }}>Which book is this?</h2>
              <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1.5rem" }}>Search by title, author, or ISBN — or enter the ISBN manually if not found</p>
              {selectedBook ? (
                <div style={{ border: "2px solid #2563eb", borderRadius: 10, padding: "1rem 1.25rem", background: "#eaf2ff", display: "flex", alignItems: "center", gap: "1rem" }}>
                  <div style={{ width: 40, height: 40, borderRadius: 8, background: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", flexShrink: 0 }}>📗</div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontWeight: 700, color: "#1f2933", margin: 0 }}>{selectedBook.title}</p>
                    <p style={{ color: "#6b7280", margin: 0, fontSize: "0.8rem" }}>{selectedBook.authors.join(", ")}</p>
                    {selectedBook.isbn_13 && <p style={{ color: "#9ca3af", margin: 0, fontSize: "0.75rem" }}>ISBN: {selectedBook.isbn_13}</p>}
                  </div>
                  <button onClick={() => setSelectedBook(null)} style={{ background: "none", border: "none", color: "#6b7280", cursor: "pointer", fontSize: "1.1rem", padding: "0.25rem" }}>✕</button>
                </div>
              ) : (
                <>
                  <div style={{ position: "relative" }}>
                    <input type="text" placeholder="e.g. Godaan, Premchand, 9780143039433..." value={bookQuery} onChange={(e) => { setBookQuery(e.target.value); searchBooks(e.target.value); }} style={inputStyle} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                    {bookSearching && <div style={{ position: "absolute", right: "0.75rem", top: "50%", transform: "translateY(-50%)", width: 16, height: 16, borderRadius: "50%", border: "2px solid #e5e7eb", borderTopColor: "#2563eb", animation: "spin 0.7s linear infinite" }} />}
                  </div>
                  {bookResults.length > 0 && (
                    <div style={{ border: "1px solid #e5e7eb", borderRadius: 8, marginTop: "0.5rem", overflow: "hidden", boxShadow: "0 4px 12px rgba(0,0,0,0.06)" }}>
                      {bookResults.map((book, i) => (
                        <button key={book.id} onClick={() => { setSelectedBook(book); setBookResults([]); setBookQuery(""); }} style={{ display: "flex", alignItems: "center", gap: "0.75rem", width: "100%", padding: "0.75rem 1rem", background: "#fff", border: "none", borderBottom: i < bookResults.length - 1 ? "1px solid #f3f4f6" : "none", cursor: "pointer", textAlign: "left" }}
                          onMouseEnter={(e) => (e.currentTarget as HTMLButtonElement).style.background = "#f9fafb"}
                          onMouseLeave={(e) => (e.currentTarget as HTMLButtonElement).style.background = "#fff"}>
                          <span style={{ fontSize: "1.25rem" }}>📗</span>
                          <div>
                            <p style={{ fontWeight: 600, color: "#1f2933", margin: 0, fontSize: "0.875rem" }}>{book.title}</p>
                            <p style={{ color: "#6b7280", margin: 0, fontSize: "0.78rem" }}>{book.authors.join(", ")}{book.publication_year ? ` · ${book.publication_year}` : ""}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                  {bookResults.length === 0 && bookQuery.length > 1 && !bookSearching && (
                    <div style={{ marginTop: "1rem", padding: "1.25rem", background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb" }}>
                      <p style={{ color: "#374151", fontWeight: 600, margin: "0 0 0.125rem", fontSize: "0.875rem" }}>Book not in our catalog?</p>
                      <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0 0 0.875rem" }}>Enter the details manually — we'll add it to the catalog for you.</p>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
                        <div>
                          <label style={labelStyle}>Book title *</label>
                          <input type="text" placeholder={bookQuery} value={manualTitle || bookQuery} onChange={(e) => setManualTitle(e.target.value)} style={{ ...inputStyle, marginTop: "0.25rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                        </div>
                        <div>
                          <label style={labelStyle}>Author <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
                          <input type="text" placeholder="e.g. Munshi Premchand" value={manualAuthor} onChange={(e) => setManualAuthor(e.target.value)} style={{ ...inputStyle, marginTop: "0.25rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                        </div>
                        <div>
                          <label style={labelStyle}>ISBN <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
                          <input type="text" placeholder="e.g. 9780143039433" value={manualIsbn} onChange={(e) => setManualIsbn(e.target.value)} style={{ ...inputStyle, marginTop: "0.25rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Step 2 — Details */}
          {step === 2 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.25rem" }}>Listing details</h2>
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>{selectedIntentOpt?.icon} {selectedIntentOpt?.title} · {selectedBook?.title ?? manualIsbn}</p>
              </div>

              {intent === "sell" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div>
                    <label style={labelStyle}>Asking price (₹) *</label>
                    <div style={{ position: "relative", marginTop: "0.375rem" }}>
                      <span style={{ position: "absolute", left: "0.875rem", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}>₹</span>
                      <input type="number" min="0" placeholder="0" value={price} onChange={(e) => setPrice(e.target.value)} style={{ ...inputStyle, paddingLeft: "2rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                    </div>
                  </div>
                  <label style={{ display: "flex", alignItems: "center", gap: "0.625rem", cursor: "pointer" }}>
                    <input type="checkbox" checked={negotiable} onChange={(e) => setNegotiable(e.target.checked)} style={{ width: 16, height: 16, accentColor: "#2563eb" }} />
                    <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 500 }}>Open to price negotiation</span>
                  </label>
                  <div style={{ background: "#f9fafb", borderRadius: 8, padding: "1rem", border: "1px solid #e5e7eb" }}>
                    <label style={{ display: "flex", alignItems: "flex-start", gap: "0.625rem", cursor: "pointer" }}>
                      <input type="checkbox" checked={openToExchange} onChange={(e) => setOpenToExchange(e.target.checked)} style={{ width: 16, height: 16, marginTop: "0.125rem", accentColor: "#2563eb" }} />
                      <div>
                        <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 600 }}>Also open to book exchange</span>
                        <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0.125rem 0 0" }}>Accept a book swap instead of money if the right offer comes along</p>
                      </div>
                    </label>
                    {openToExchange && (
                      <div style={{ marginTop: "0.875rem" }}>
                        <label style={labelStyle}>What books would you want in return?</label>
                        <input type="text" placeholder="e.g. Any CS textbook, Indian fiction novels..." value={exchangePrefs} onChange={(e) => setExchangePrefs(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {intent === "exchange" && (
                <div>
                  <label style={labelStyle}>What are you looking for in return?</label>
                  <input type="text" placeholder="e.g. Any semester 3 CS textbook, fiction by Indian authors..." value={exchangePrefs} onChange={(e) => setExchangePrefs(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                  <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0.5rem 0 0" }}>Leave blank if you're open to any book</p>
                </div>
              )}

              {intent === "give_away" && (
                <div style={{ background: "#f5f3ff", borderRadius: 8, padding: "1rem 1.25rem", border: "1px solid #e9d5ff" }}>
                  <p style={{ fontWeight: 600, color: "#7c3aed", margin: "0 0 0.25rem", fontSize: "0.875rem" }}>🎁 Giving it away for free</p>
                  <p style={{ color: "#6b7280", fontSize: "0.825rem", margin: 0 }}>This book will be listed as a free donation. No payment will be expected.</p>
                </div>
              )}

              {intent === "lend_rent" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div>
                    <label style={labelStyle}>Maximum borrowing duration *</label>
                    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
                      {[7, 14, 30, 60, 90].map((days) => (
                        <button key={days} onClick={() => setLendingDays(String(days))} style={{ padding: "0.4rem 0.875rem", borderRadius: 6, fontSize: "0.825rem", fontWeight: 500, border: `1.5px solid ${lendingDays === String(days) ? "#2563eb" : "#e5e7eb"}`, background: lendingDays === String(days) ? "#eaf2ff" : "#fff", color: lendingDays === String(days) ? "#2563eb" : "#374151", cursor: "pointer", transition: "all 0.15s" }}>
                          {days} days
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ background: "#f9fafb", borderRadius: 8, padding: "1rem", border: "1px solid #e5e7eb" }}>
                    <label style={{ display: "flex", alignItems: "flex-start", gap: "0.625rem", cursor: "pointer" }}>
                      <input type="checkbox" checked={chargeRent} onChange={(e) => setChargeRent(e.target.checked)} style={{ width: 16, height: 16, marginTop: "0.125rem", accentColor: "#2563eb" }} />
                      <div>
                        <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 600 }}>Charge a daily rental fee</span>
                        <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0.125rem 0 0" }}>Leave unchecked to lend for free</p>
                      </div>
                    </label>
                    {chargeRent && (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginTop: "0.875rem" }}>
                        <div>
                          <label style={labelStyle}>Fee per day (₹)</label>
                          <div style={{ position: "relative", marginTop: "0.375rem" }}>
                            <span style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}>₹</span>
                            <input type="number" min="0" placeholder="10" value={rentPerDay} onChange={(e) => setRentPerDay(e.target.value)} style={{ ...inputStyle, paddingLeft: "1.75rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                          </div>
                        </div>
                        <div>
                          <label style={labelStyle}>Refundable deposit (₹) <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
                          <div style={{ position: "relative", marginTop: "0.375rem" }}>
                            <span style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}>₹</span>
                            <input type="number" min="0" placeholder="0" value={deposit} onChange={(e) => setDeposit(e.target.value)} style={{ ...inputStyle, paddingLeft: "1.75rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {!isRequest && (
                <div>
                  <label style={labelStyle}>Book condition *</label>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "0.5rem" }}>
                    {CONDITIONS.map((c) => (
                      <button key={c.key} onClick={() => setCondition(c.key)} style={{ display: "flex", alignItems: "center", gap: "0.875rem", padding: "0.75rem 1rem", border: `1.5px solid ${condition === c.key ? c.color : "#e5e7eb"}`, borderRadius: 8, background: condition === c.key ? `${c.color}08` : "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.15s" }}>
                        <div style={{ width: 10, height: 10, borderRadius: "50%", background: c.color, flexShrink: 0 }} />
                        <div style={{ flex: 1 }}>
                          <span style={{ fontWeight: 600, color: "#1f2933", fontSize: "0.875rem" }}>{c.label}</span>
                          <span style={{ color: "#6b7280", fontSize: "0.8rem", marginLeft: "0.5rem" }}>{c.desc}</span>
                        </div>
                        {condition === c.key && <span style={{ color: c.color, fontWeight: 700, fontSize: "0.875rem" }}>✓</span>}
                      </button>
                    ))}
                  </div>
                  {condition && !["new_sealed", "like_new"].includes(condition) && (
                    <div style={{ marginTop: "1rem", background: "#f9fafb", padding: "1rem", borderRadius: 8, border: "1px solid #e5e7eb" }}>
                      <p style={{ fontWeight: 600, color: "#374151", margin: "0 0 0.75rem", fontSize: "0.825rem" }}>Any defects? (tick all that apply)</p>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                        {(Object.keys(conditionFlags) as (keyof typeof conditionFlags)[]).map((flag) => (
                          <label key={flag} style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.825rem", color: "#374151" }}>
                            <input type="checkbox" checked={conditionFlags[flag]} onChange={(e) => setConditionFlags((f) => ({ ...f, [flag]: e.target.checked }))} style={{ accentColor: "#2563eb" }} />
                            {flag.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div>
                <label style={labelStyle}>Description <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
                <textarea rows={3} placeholder={isRequest ? "Edition preferences, how soon you need it, your budget range..." : "Any extra details about this copy, why you're listing it..."} value={description} onChange={(e) => setDescription(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem", resize: "vertical", minHeight: 80, fontFamily: "inherit" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
              </div>
            </div>
          )}

          {/* Step 3 — Scope & Visibility */}
          {step === 3 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.25rem" }}>Who is this listing for?</h2>
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>Choose where this book belongs and who can see it</p>
              </div>

              {/* Scope */}
              <div>
                <label style={{ ...labelStyle, display: "block", marginBottom: "0.625rem" }}>List this book under</label>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>

                  {/* Personal */}
                  <button onClick={() => { setScope("personal"); setVisibility("public"); }} style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1rem 1.25rem", border: `2px solid ${scope === "personal" ? "#2563eb" : "#e5e7eb"}`, borderRadius: 10, background: scope === "personal" ? "#eaf2ff" : "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.15s" }}>
                    <div style={{ width: 40, height: 40, borderRadius: 8, background: scope === "personal" ? "#2563eb" : "#f9fafb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", flexShrink: 0, transition: "background 0.15s" }}>👤</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 700, color: "#1f2933", margin: 0, fontSize: "0.9rem" }}>My personal listing</p>
                      <p style={{ color: "#6b7280", margin: 0, fontSize: "0.8rem" }}>Listed under your personal profile</p>
                    </div>
                    {scope === "personal" && <span style={{ color: "#2563eb", fontWeight: 700 }}>✓</span>}
                  </button>

                  {/* Business */}
                  <button
                    onClick={() => myBusiness ? (setScope("business"), setVisibility("public")) : undefined}
                    disabled={!myBusiness}
                    style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1rem 1.25rem", border: `2px solid ${scope === "business" ? "#2563eb" : "#e5e7eb"}`, borderRadius: 10, background: scope === "business" ? "#eff6ff" : !myBusiness ? "#f9fafb" : "#fff", cursor: myBusiness ? "pointer" : "not-allowed", textAlign: "left", transition: "all 0.15s", opacity: !myBusiness ? 0.6 : 1 }}
                  >
                    <div style={{ width: 40, height: 40, borderRadius: 8, background: scope === "business" ? "#2563eb" : "#f9fafb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", flexShrink: 0 }}>🏪</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 700, color: "#1f2933", margin: 0, fontSize: "0.9rem" }}>
                        My business{myBusiness ? ` — ${myBusiness.name}` : ""}
                      </p>
                      <p style={{ color: "#6b7280", margin: 0, fontSize: "0.8rem" }}>
                        {myBusiness ? "Listed under your business profile" : "You don't have an active business yet"}
                      </p>
                    </div>
                    {scope === "business" && <span style={{ color: "#2563eb", fontWeight: 700 }}>✓</span>}
                    {!myBusiness && <Link href="/business" onClick={(e) => e.stopPropagation()} style={{ fontSize: "0.75rem", color: "#2563eb", whiteSpace: "nowrap" }}>Set up →</Link>}
                  </button>

                  {/* Institution */}
                  <button
                    onClick={() => myInstitution ? (setScope("institution"), setVisibility("public")) : undefined}
                    disabled={!myInstitution}
                    style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "1rem 1.25rem", border: `2px solid ${scope === "institution" ? "#9333ea" : "#e5e7eb"}`, borderRadius: 10, background: scope === "institution" ? "#faf5ff" : !myInstitution ? "#f9fafb" : "#fff", cursor: myInstitution ? "pointer" : "not-allowed", textAlign: "left", transition: "all 0.15s", opacity: !myInstitution ? 0.6 : 1 }}
                  >
                    <div style={{ width: 40, height: 40, borderRadius: 8, background: scope === "institution" ? "#9333ea" : "#f9fafb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", flexShrink: 0 }}>🏫</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 700, color: "#1f2933", margin: 0, fontSize: "0.9rem" }}>
                        My institution{myInstitution ? ` — ${myInstitution.name}` : ""}
                      </p>
                      <p style={{ color: "#6b7280", margin: 0, fontSize: "0.8rem" }}>
                        {myInstitution ? "Listed under your institution" : "You don't have an active institution yet"}
                      </p>
                    </div>
                    {scope === "institution" && <span style={{ color: "#9333ea", fontWeight: 700 }}>✓</span>}
                    {!myInstitution && <Link href="/institution" onClick={(e) => e.stopPropagation()} style={{ fontSize: "0.75rem", color: "#9333ea", whiteSpace: "nowrap" }}>Set up →</Link>}
                  </button>
                </div>
              </div>

              {/* Visibility */}
              <div>
                <label style={{ ...labelStyle, display: "block", marginBottom: "0.625rem" }}>Who can see this listing?</label>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {scope === "personal" && (
                    <>
                      <VisibilityOption value="public" current={visibility} onChange={setVisibility} icon="🌍" title="Everyone on OldPages" desc="Visible in search results to all users on the platform" color="#2563eb" />
                      <VisibilityOption value="private" current={visibility} onChange={setVisibility} icon="🔒" title="Only me" desc="Private — only you can see this listing. Like a personal draft." color="#374151" />
                    </>
                  )}
                  {scope === "business" && (
                    <>
                      <VisibilityOption value="public" current={visibility} onChange={setVisibility} icon="🌍" title="Everyone on OldPages" desc="Visible in search results to all users — great for selling or reaching more buyers" color="#2563eb" />
                      <VisibilityOption value="business_only" current={visibility} onChange={setVisibility} icon="🏪" title="Business staff only" desc="Only your business staff members can see this — for internal inventory management" color="#2563eb" />
                    </>
                  )}
                  {scope === "institution" && (
                    <>
                      <VisibilityOption value="public" current={visibility} onChange={setVisibility} icon="🌍" title="Everyone on OldPages" desc="Visible in search results to all users" color="#2563eb" />
                      <VisibilityOption value="institution_only" current={visibility} onChange={setVisibility} icon="🏫" title="Institution members only" desc="Only students, staff, and alumni of your institution can see this" color="#9333ea" />
                    </>
                  )}
                </div>
              </div>

              {/* Summary banner */}
              <div style={{ background: "#eaf2ff", borderRadius: 8, padding: "0.875rem 1rem", border: "1px solid #a7f3d0" }}>
                <p style={{ color: "#065f46", fontSize: "0.825rem", margin: 0, lineHeight: 1.6 }}>
                  {visibility === "public" && "🌍 This listing will be visible to everyone searching on OldPages."}
                  {visibility === "private" && "🔒 Only you can see this listing. Perfect for tracking books you own."}
                  {visibility === "business_only" && `🏪 Only ${myBusiness?.name ?? "your business"} staff can see this listing.`}
                  {visibility === "institution_only" && `🏫 Only members of ${myInstitution?.name ?? "your institution"} can see this listing.`}
                </p>
              </div>
            </div>
          )}

          {/* Step 4 — Location (was 3) */}
          {step === 4 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.25rem" }}>Where are you located?</h2>
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>Helps nearby readers find your listing first</p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div>
                  <label style={labelStyle}>City *</label>
                  <input type="text" placeholder="Pune" value={city} onChange={(e) => setCity(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                </div>
                <div>
                  <label style={labelStyle}>State</label>
                  <input type="text" placeholder="Maharashtra" value={state} onChange={(e) => setState(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
                </div>
              </div>
              <div>
                <label style={labelStyle}>Area / Neighbourhood <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
                <input type="text" placeholder="e.g. Deccan, Kothrud, FC Road..." value={neighborhood} onChange={(e) => setNeighborhood(e.target.value)} style={{ ...inputStyle, marginTop: "0.375rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
              </div>
              <div style={{ background: "#f9fafb", borderRadius: 8, padding: "1.25rem", border: "1px solid #e5e7eb" }}>
                <p style={{ fontWeight: 600, color: "#374151", margin: "0 0 0.875rem", fontSize: "0.875rem" }}>How can readers receive this book?</p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
                  <label style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem", cursor: "pointer" }}>
                    <input type="checkbox" checked={campusPickup} onChange={(e) => setCampusPickup(e.target.checked)} style={{ width: 16, height: 16, marginTop: "0.125rem", accentColor: "#2563eb" }} />
                    <div>
                      <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 600 }}>📍 In-person / Campus pickup</span>
                      <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0.125rem 0 0" }}>Meet at a safe public spot — campus library, café, hostel entrance</p>
                    </div>
                  </label>
                  <label style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem", cursor: "pointer" }}>
                    <input type="checkbox" checked={offersShipping} onChange={(e) => setOffersShipping(e.target.checked)} style={{ width: 16, height: 16, marginTop: "0.125rem", accentColor: "#2563eb" }} />
                    <div>
                      <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 600 }}>📦 Ship anywhere in India</span>
                      <p style={{ color: "#6b7280", fontSize: "0.78rem", margin: "0.125rem 0 0" }}>Courier or postal delivery — buyer pays shipping unless you specify otherwise</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Step 5 — Review */}
          {step === 5 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1f2933", margin: 0 }}>Review your listing</h2>
              {error && (
                <div style={{ background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 8, padding: "0.75rem 1rem", display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
                  <span style={{ color: "#e11d48", flexShrink: 0 }}>✕</span>
                  <p style={{ color: "#be123c", fontSize: "0.875rem", margin: 0 }}>{error}</p>
                </div>
              )}
              <div style={{ border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
                {[
                  { label: "Intent", value: `${selectedIntentOpt?.icon} ${selectedIntentOpt?.title}` },
                  { label: "Book", value: selectedBook ? `${selectedBook.title} — ${selectedBook.authors.join(", ")}` : manualIsbn },
                  { label: "Condition", value: !isRequest ? CONDITIONS.find((c) => c.key === condition)?.label ?? "—" : "N/A" },
                  { label: "Price", value: isFree ? "Free" : intent === "lend_rent" ? (chargeRent && rentPerDay ? `₹${rentPerDay}/day${deposit ? ` + ₹${deposit} deposit` : ""}` : "Free to borrow") : price ? `₹${price}${negotiable ? " (negotiable)" : ""}` : "—" },
                  ...(intent === "lend_rent" ? [{ label: "Duration", value: `Up to ${lendingDays} days` }] : []),
                  ...(openToExchange || intent === "exchange" ? [{ label: "Exchange", value: exchangePrefs || "Open to any book" }] : []),
                  { label: "Location", value: [neighborhood, city, state].filter(Boolean).join(", ") || city },
                  { label: "Delivery", value: [campusPickup && "Pickup", offersShipping && "Shipping"].filter(Boolean).join(" & ") || "—" },
                  { label: "Listed under", value: scope === "personal" ? "My profile" : scope === "business" ? `Business — ${myBusiness?.name ?? ""}` : `Institution — ${myInstitution?.name ?? ""}` },
                  { label: "Visible to", value: visibility === "public" ? "Everyone on OldPages" : visibility === "private" ? "Only me" : visibility === "business_only" ? "Business staff only" : "Institution members only" },
                ].map((row, i, arr) => (
                  <div key={row.label} style={{ display: "flex", padding: "0.75rem 1rem", borderBottom: i < arr.length - 1 ? "1px solid #f3f4f6" : "none", gap: "1rem" }}>
                    <span style={{ width: 110, flexShrink: 0, fontSize: "0.8rem", color: "#6b7280", fontWeight: 500 }}>{row.label}</span>
                    <span style={{ fontSize: "0.875rem", color: "#1f2933", fontWeight: 500 }}>{row.value}</span>
                  </div>
                ))}
              </div>
              {description && (
                <div style={{ background: "#f9fafb", borderRadius: 8, padding: "0.875rem 1rem", border: "1px solid #e5e7eb" }}>
                  <p style={{ fontSize: "0.72rem", fontWeight: 700, color: "#6b7280", margin: "0 0 0.375rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>Description</p>
                  <p style={{ color: "#374151", fontSize: "0.875rem", margin: 0, lineHeight: 1.65 }}>{description}</p>
                </div>
              )}
              <div style={{ background: "#eaf2ff", borderRadius: 8, padding: "0.875rem 1rem", border: "1px solid #a7f3d0" }}>
                <p style={{ color: "#065f46", fontSize: "0.8rem", margin: 0 }}>
                  🚀 Your listing will go live immediately and reach readers near <strong>{city}</strong>.
                </p>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid #f3f4f6" }}>
            <button onClick={() => step > 0 ? setStep(step - 1) : router.back()} style={{ padding: "0.7rem 1.25rem", borderRadius: 8, border: "1.5px solid #e5e7eb", background: "#fff", color: "#374151", fontWeight: 600, fontSize: "0.875rem", cursor: "pointer" }}>
              {step === 0 ? "Cancel" : "← Back"}
            </button>
            {step < 5 ? (
              <button onClick={() => canContinue && setStep(step + 1)} disabled={!canContinue} style={{ padding: "0.7rem 1.75rem", borderRadius: 8, border: "none", background: canContinue ? "#2563eb" : "#d1d5db", color: "white", fontWeight: 700, fontSize: "0.875rem", cursor: canContinue ? "pointer" : "not-allowed", transition: "background 0.15s" }}>
                Continue →
              </button>
            ) : (
              <button onClick={submit} disabled={submitting} style={{ padding: "0.7rem 1.75rem", borderRadius: 8, border: "none", background: "#2563eb", color: "white", fontWeight: 700, fontSize: "0.875rem", cursor: submitting ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: "0.5rem", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? <><div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "white", animation: "spin 0.7s linear infinite" }} /> Publishing…</> : "🚀 Publish Listing"}
              </button>
            )}
          </div>
        </div>
      </Container>
    </div>
  );
}
