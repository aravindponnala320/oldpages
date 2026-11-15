"use client";

import { useEffect, useState } from "react";
import type {
  CategoryLevelsResponse,
  CategoryOption,
} from "@oldpages/shared-types";
import { apiClient } from "../lib/api";
import { colors, font, radius } from "./ui";

// Dropdown lists don't change while the page is open; keep each answer.
const cache = new Map<string, Promise<CategoryLevelsResponse>>();

function loadLevels(slug: string | null): Promise<CategoryLevelsResponse> {
  const key = slug ?? "";
  let pending = cache.get(key);
  if (!pending) {
    pending = apiClient.getCategoryLevels(slug);
    pending.catch(() => cache.delete(key));
    cache.set(key, pending);
  }
  return pending;
}

export type CategoryPickerProps = {
  value: string | null;
  onChange?: (slug: string | null, path: CategoryOption[]) => void;
  /** "form" asks the seller to choose; "filter" offers "All …" at every step. */
  mode?: "form" | "filter";
  /** Submit the chosen slug with a plain <form> under this name. */
  name?: string;
  /** Lay dropdowns side by side when there's room (Sell form); stacked otherwise. */
  columns?: boolean;
};

/**
 * Cascading category dropdowns: Category → (Type → Board → Class → Subject …).
 * Each next dropdown appears only once the one before it has a choice.
 */
export function CategoryPicker({
  value,
  onChange,
  mode = "form",
  name,
  columns = false,
}: CategoryPickerProps) {
  const [slug, setSlug] = useState<string | null>(value);
  const [data, setData] = useState<CategoryLevelsResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => setSlug(value), [value]);

  useEffect(() => {
    let live = true;
    loadLevels(slug)
      .then((d) => {
        if (live) {
          setData(d);
          setError(false);
        }
      })
      .catch(() => {
        if (live) setError(true);
      });
    return () => {
      live = false;
    };
  }, [slug]);

  function choose(levelIndex: number, picked: string) {
    // An empty choice steps back to the dropdown's parent.
    const next = picked || data?.levels[levelIndex]?.parent_slug || null;
    setSlug(next);
    loadLevels(next)
      .then((d) => onChange?.(next, d.path))
      .catch(() => undefined);
  }

  if (error && !data) {
    return (
      <p
        style={{ margin: 0, fontSize: font.size.sm, color: colors.dangerText }}
      >
        Couldn&apos;t load categories. Check your connection and reload.
      </p>
    );
  }

  const levels = data?.levels ?? [];
  const path = data?.path ?? [];
  const filter = mode === "filter";

  return (
    <div>
      {name && <input type="hidden" name={name} value={slug ?? ""} />}
      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: columns
            ? "repeat(auto-fill, minmax(min(100%, 210px), 1fr))"
            : "minmax(0, 1fr)",
        }}
      >
        {(data
          ? levels
          : [{ label: "Category", options: [], parent_slug: null }]
        ).map((level, i) => {
          const selected = path[i]?.slug ?? "";
          const lower = level.label.toLowerCase();
          const placeholder = filter
            ? i === 0
              ? "All categories"
              : `Any ${lower}`
            : i === 0
              ? "Choose a category"
              : `Choose ${lower}`;
          return (
            <label
              key={level.parent_slug ?? "root"}
              className="op-cat-level"
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                minWidth: 0,
              }}
            >
              <span
                style={{
                  fontSize: font.size.sm,
                  fontWeight: font.weight.semibold,
                  color: colors.textMuted,
                }}
              >
                {level.label}
                {!filter && i > 0 && (
                  <span style={{ fontWeight: 400, color: colors.textSubtle }}>
                    {" "}
                    (optional)
                  </span>
                )}
              </span>
              <select
                value={selected}
                disabled={!data}
                onChange={(e) => choose(i, e.target.value)}
                style={{
                  width: "100%",
                  minWidth: 0,
                  height: 42,
                  padding: "0 12px",
                  border: `1px solid ${selected ? colors.primary : colors.borderStrong}`,
                  borderRadius: radius.md,
                  background: colors.surface,
                  color: selected ? colors.text : colors.textMuted,
                  fontSize: 16, // no iOS zoom on focus
                  textOverflow: "ellipsis",
                }}
              >
                <option value="">{placeholder}</option>
                {level.options.map((o) => (
                  <option key={o.slug} value={o.slug}>
                    {o.name}
                  </option>
                ))}
              </select>
            </label>
          );
        })}
      </div>

      {!filter && path.length > 1 && (
        <p
          style={{
            margin: "14px 0 0",
            padding: "10px 12px",
            borderRadius: radius.md,
            background: colors.primarySoft,
            fontSize: font.size.sm,
            lineHeight: 1.5,
            color: colors.text,
            fontWeight: font.weight.medium,
          }}
        >
          {path.map((p) => p.name).join(" › ")}
        </p>
      )}
    </div>
  );
}
