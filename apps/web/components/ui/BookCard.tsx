"use client";

import Link from "next/link";
import { useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { colors, font, radius } from "./theme";
import { ConditionBadge } from "./Badge";
import { Icon } from "./Icon";

export type BookCardData = {
  id: string;
  href: string;
  title: string;
  author?: string | null;
  imageUrl?: string | null;
  priceLabel?: string | null;
  condition?: string | null;
  location?: string | null;
};

/** Renders a book card, used in grids across the app. */
export function BookCard({ book, style }: { book: BookCardData; style?: CSSProperties }) {
  return (
    <Link
      href={book.href}
      style={{
        textDecoration: "none",
        color: "inherit",
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.lg,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        transition: "transform 0.15s, box-shadow 0.15s",
        ...style,
      }}
    >
      <BookCover imageUrl={book.imageUrl} title={book.title} seed={book.id} author={book.author} />
      <div style={{ padding: "10px 12px 12px", display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
        <h3
          style={{
            margin: 0,
            fontSize: font.size.sm,
            fontWeight: font.weight.semibold,
            color: colors.text,
            lineHeight: font.lineHeight.snug,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            minHeight: 34,
          }}
        >
          {book.title}
        </h3>
        {book.author && (
          <p
            style={{
              margin: 0,
              fontSize: font.size.sm,
              color: colors.textSubtle,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {book.author}
          </p>
        )}
        {book.condition && (
          <div style={{ marginTop: 4 }}>
            <ConditionBadge condition={book.condition} />
          </div>
        )}
        <div
          style={{
            marginTop: "auto",
            paddingTop: 8,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>
            {book.priceLabel ?? ""}
          </span>
          {book.location && (
            <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: font.size.xs, color: colors.textFaint }}>
              <Icon.pin size={12} color={colors.textFaint} /> {book.location}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

/**
 * Book cover that renders the real image when available, otherwise a
 * deterministic gradient placeholder with the title's initials.
 *
 * Also falls back to the placeholder if the image URL fails to load
 * (e.g. broken storage link).
 */
export function BookCover({
  imageUrl,
  title,
  author,
  seed,
  overlay,
  aspectRatio = "3/4",
}: {
  imageUrl?: string | null;
  title: string;
  author?: string | null;
  seed?: string;
  overlay?: ReactNode;
  aspectRatio?: string;
}) {
  const [broken, setBroken] = useState(false);
  const shouldShowPlaceholder = !imageUrl || broken;
  const design = useMemo(() => pickDesign(seed || title), [seed, title]);
  const glyph = useMemo(() => initials(title), [title]);

  return (
    <div
      style={{
        aspectRatio,
        position: "relative",
        overflow: "hidden",
        background: shouldShowPlaceholder ? design.background : "#f5f6f8",
        display: "flex",
        alignItems: "stretch",
        justifyContent: "stretch",
      }}
    >
      {imageUrl && !broken && (
        <img
          src={imageUrl}
          alt={title}
          onError={() => setBroken(true)}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
        />
      )}
      {shouldShowPlaceholder && (
        <Placeholder design={design} glyph={glyph} title={title} author={author ?? null} />
      )}
      {overlay}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Placeholder helpers                                                 */
/* ------------------------------------------------------------------ */

type Design = {
  id: number;
  background: string;
  text: string;
  accent: string;
  spineTone: string;
  pattern: "spine" | "corner" | "band" | "dots";
};

const PALETTES: Omit<Design, "pattern" | "id">[] = [
  { background: "linear-gradient(135deg, #5B21B6 0%, #7C3AED 100%)", text: "#F5F3FF", accent: "#C4B5FD", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)", text: "#F0FDFA", accent: "#5EEAD4", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #B91C1C 0%, #EF4444 100%)", text: "#FEF2F2", accent: "#FCA5A5", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%)", text: "#EFF6FF", accent: "#93C5FD", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #92400E 0%, #F59E0B 100%)", text: "#FFFBEB", accent: "#FCD34D", spineTone: "rgba(0,0,0,0.14)" },
  { background: "linear-gradient(135deg, #831843 0%, #EC4899 100%)", text: "#FDF2F8", accent: "#F9A8D4", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #064E3B 0%, #10B981 100%)", text: "#ECFDF5", accent: "#6EE7B7", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #4C1D95 0%, #6366F1 100%)", text: "#EEF2FF", accent: "#A5B4FC", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #7C2D12 0%, #EA580C 100%)", text: "#FFF7ED", accent: "#FDBA74", spineTone: "rgba(0,0,0,0.12)" },
  { background: "linear-gradient(135deg, #164E63 0%, #06B6D4 100%)", text: "#ECFEFF", accent: "#67E8F9", spineTone: "rgba(255,255,255,0.14)" },
  { background: "linear-gradient(135deg, #365314 0%, #84CC16 100%)", text: "#F7FEE7", accent: "#BEF264", spineTone: "rgba(0,0,0,0.12)" },
  { background: "linear-gradient(135deg, #1F2937 0%, #4B5563 100%)", text: "#F9FAFB", accent: "#D1D5DB", spineTone: "rgba(255,255,255,0.12)" },
];

const PATTERNS: Design["pattern"][] = ["spine", "corner", "band", "dots"];
const STOP_WORDS = new Set(["the", "a", "an", "of", "and", "in", "on", "to", "for"]);

function pickDesign(seed: string): Design {
  const h = hash(seed);
  const palette = PALETTES[h % PALETTES.length] ?? PALETTES[0]!;
  const pattern =
    PATTERNS[Math.floor(h / PALETTES.length) % PATTERNS.length] ?? "spine";
  return { id: h, ...palette, pattern };
}

function hash(s: string): number {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
  return h;
}

function initials(title: string): string {
  const cleaned = title.trim();
  if (!cleaned) return "?";
  const words = cleaned
    .split(/\s+/)
    .filter((w) => !STOP_WORDS.has(w.toLowerCase()));
  const usable = words.length > 0 ? words : cleaned.split(/\s+/);
  const first = usable[0]?.[0] ?? "?";
  const second = usable[1]?.[0] ?? "";
  return (first + second).toUpperCase().slice(0, 2);
}

function Placeholder({
  design,
  glyph,
  title,
  author,
}: {
  design: Design;
  glyph: string;
  title: string;
  author: string | null;
}) {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        color: design.text,
        userSelect: "none",
      }}
    >
      {/* Decorative pattern layer */}
      <PatternLayer design={design} />

      {/* Left spine strip — reads like a book edge */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: 0,
          width: 6,
          background: design.spineTone,
          borderRight: `1px solid ${design.spineTone}`,
        }}
      />

      {/* Centered initials */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 12px",
        }}
      >
        <span
          style={{
            fontSize: "clamp(2.4rem, 6vw, 4rem)",
            fontWeight: 800,
            letterSpacing: "-0.02em",
            lineHeight: 1,
            color: design.text,
            textShadow: "0 2px 8px rgba(0,0,0,0.18)",
          }}
        >
          {glyph}
        </span>
      </div>

      {/* Title strip along the bottom (like a book label) */}
      <div
        style={{
          padding: "10px 12px 12px",
          background:
            "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.22) 100%)",
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: design.accent,
            marginBottom: 2,
          }}
        >
          {author ? author : "Book"}
        </div>
        <div
          style={{
            fontSize: 13,
            fontWeight: 700,
            lineHeight: 1.2,
            color: design.text,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {title}
        </div>
      </div>
    </div>
  );
}

function PatternLayer({ design }: { design: Design }) {
  const base: CSSProperties = {
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
    opacity: 0.85,
  };
  switch (design.pattern) {
    case "spine":
      return (
        <div
          style={{
            ...base,
            backgroundImage: `repeating-linear-gradient(180deg, ${design.spineTone} 0px, ${design.spineTone} 1px, transparent 1px, transparent 14px)`,
          }}
        />
      );
    case "corner":
      return (
        <div
          style={{
            ...base,
            background: `radial-gradient(circle at top right, ${design.accent}33 0%, transparent 55%)`,
          }}
        />
      );
    case "band":
      return (
        <div
          style={{
            position: "absolute",
            top: "38%",
            left: 0,
            right: 0,
            height: 6,
            background: design.accent,
            opacity: 0.4,
            pointerEvents: "none",
          }}
        />
      );
    case "dots":
      return (
        <div
          style={{
            ...base,
            backgroundImage: `radial-gradient(${design.accent}55 1.2px, transparent 1.5px)`,
            backgroundSize: "14px 14px",
            opacity: 0.35,
          }}
        />
      );
  }
}
