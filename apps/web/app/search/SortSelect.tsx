"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { colors, font, radius } from "../../components/ui";

/** Sort control above the results; changing it reloads the search with the same filters. */
export function SortSelect({
  value,
  options,
}: {
  value: string;
  options: { value: string; label: string }[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: font.size.sm,
        color: colors.textMuted,
        whiteSpace: "nowrap",
      }}
    >
      Sort
      <select
        value={value}
        onChange={(e) => {
          const next = new URLSearchParams(params.toString());
          next.set("sort", e.target.value);
          next.delete("cursor");
          router.push(`${pathname}?${next.toString()}`);
        }}
        style={{
          height: 36,
          padding: "0 10px",
          border: `1px solid ${colors.borderStrong}`,
          borderRadius: radius.md,
          background: colors.surface,
          color: colors.text,
          fontSize: font.size.sm,
          maxWidth: "100%",
        }}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
