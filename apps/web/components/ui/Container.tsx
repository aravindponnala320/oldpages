import type { CSSProperties, ReactNode } from "react";
import { layout } from "./theme";

type Props = {
  children: ReactNode;
  maxWidth?: number;
  padded?: boolean;
  style?: CSSProperties;
};

export function Container({ children, maxWidth = layout.maxWidth, padded = true, style }: Props) {
  return (
    <div
      style={{
        maxWidth,
        margin: "0 auto",
        padding: padded ? `0 ${layout.gutter}px` : 0,
        width: "100%",
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
