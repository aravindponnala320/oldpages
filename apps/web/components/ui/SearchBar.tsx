"use client";

import type { CSSProperties } from "react";
import { colors, radius } from "./theme";
import { Icon } from "./Icon";

type Props = {
  placeholder?: string;
  action?: string;
  name?: string;
  defaultValue?: string;
  maxWidth?: number;
  style?: CSSProperties;
};

/**
 * Home-page-style search bar: pill outline with a filled circular search button on the right.
 * Server-friendly — submits as a GET form so it can be used outside "use client" pages.
 */
export function SearchBar({
  placeholder = "Search books by title, author, ISBN...",
  action = "/search",
  name = "q",
  defaultValue = "",
  maxWidth = 640,
  style,
}: Props) {
  return (
    <form
      action={action}
      method="GET"
      style={{
        flex: 1,
        maxWidth,
        display: "flex",
        alignItems: "center",
        background: colors.surface,
        border: `1px solid ${colors.borderStrong}`,
        borderRadius: radius.pill,
        padding: "6px 6px 6px 20px",
        gap: 10,
        ...style,
      }}
    >
      <Icon.search color={colors.textFaint} />
      <input
        type="text"
        name={name}
        defaultValue={defaultValue}
        placeholder={placeholder}
        style={{
          flex: 1,
          border: "none",
          outline: "none",
          background: "transparent",
          padding: "10px 4px",
          fontSize: 14,
          color: colors.text,
          minWidth: 0,
        }}
      />
      <button
        type="submit"
        aria-label="Search"
        style={{
          width: 40,
          height: 40,
          borderRadius: "50%",
          background: colors.primary,
          border: "none",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          flexShrink: 0,
        }}
      >
        <Icon.search size={16} color="#fff" />
      </button>
    </form>
  );
}
