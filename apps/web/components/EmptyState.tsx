import type { ReactNode } from "react";
import { EmptyState as UIEmptyState } from "./ui/EmptyState";

/** Back-compat wrapper. Prefer importing from `components/ui/EmptyState`. */
export function EmptyState({
  title,
  body,
  icon,
  action,
}: {
  title: string;
  body: string;
  icon?: string | ReactNode;
  action?: ReactNode;
}) {
  const iconNode =
    typeof icon === "string" ? <span style={{ fontSize: 28 }}>{icon}</span> : icon;
  return <UIEmptyState title={title} description={body} icon={iconNode} action={action} />;
}
