// Mirrors the API's `disabled_listing_modes` setting: lending, renting and book
// requests are switched off for launch. The API rejects and hides them either way;
// this only keeps the UI from offering them.
export const DISABLED_LISTING_MODES: ReadonlySet<string> = new Set([
  "lend",
  "rent",
  "request",
]);

export function isModeEnabled(mode: string): boolean {
  return !DISABLED_LISTING_MODES.has(mode);
}
