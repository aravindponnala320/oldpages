import type { CategoryOption } from "@oldpages/shared-types";

/** "CBSE › Class 10 › Science": the last few steps of a category path. */
export function categoryTrail(path: CategoryOption[], keep = 3): string {
  return path
    .slice(-keep)
    .map((p) => p.name)
    .join(" › ");
}
