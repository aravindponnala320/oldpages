export const ACCESS_TOKEN_KEY = "op_access_token";
export const REFRESH_TOKEN_KEY = "op_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// Public user id (not a secret) for server-rendered pages, e.g. search hides your own books.
export const VIEWER_COOKIE = "op_uid";

export function setViewerCookie(userId: string | null): void {
  if (typeof document === "undefined") return;
  document.cookie = userId
    ? `${VIEWER_COOKIE}=${encodeURIComponent(userId)}; Path=/; Max-Age=${60 * 60 * 24 * 30}; SameSite=Lax`
    : `${VIEWER_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}
