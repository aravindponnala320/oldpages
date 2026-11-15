// Content-Security-Policy for the web app. Sign-in tokens live in localStorage, so the
// policy's job is to stop injected script from running: only scripts carrying this
// request's nonce (and what they load, via 'strict-dynamic') may execute.

const GOOGLE_SIGN_IN = "https://accounts.google.com";

function origin(url: string | undefined): string | null {
  if (!url) return null;
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

function socketOrigin(httpOrigin: string): string {
  return httpOrigin.replace(/^http/, "ws");
}

export type CspEnv = {
  apiBaseUrl?: string;
  /** Where photos are uploaded and served from (MinIO locally, the bucket in production). */
  mediaBaseUrl?: string;
  development: boolean;
};

export function buildCsp(nonce: string, env: CspEnv): string {
  const api = origin(env.apiBaseUrl);
  const media = origin(env.mediaBaseUrl);
  const connect = ["'self'", GOOGLE_SIGN_IN];
  if (api) connect.push(api, socketOrigin(api));
  // Without a configured bucket address, keep photo uploads working over any https host.
  connect.push(media ?? "https:");
  if (env.development) connect.push("ws:", "http://localhost:*");

  const directives: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": [
      `'nonce-${nonce}'`,
      "'strict-dynamic'",
      // Ignored by browsers that understand 'strict-dynamic'; a fallback for older ones.
      "'self'",
      "https:",
      ...(env.development ? ["'unsafe-eval'"] : []),
    ],
    "style-src": ["'self'", "'unsafe-inline'", GOOGLE_SIGN_IN],
    "img-src": [
      "'self'",
      "data:",
      "blob:",
      "https:",
      ...(media ? [media] : []),
      ...(env.development ? ["http://localhost:*"] : []),
    ],
    "font-src": ["'self'", "data:"],
    "connect-src": connect,
    "frame-src": [GOOGLE_SIGN_IN],
    "media-src": ["'self'", "blob:"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
  };
  const policy = Object.entries(directives).map(
    ([name, values]) => `${name} ${values.join(" ")}`,
  );
  // Only once the site is served over https; a local production build talks plain http.
  if (!env.development && api?.startsWith("https:")) {
    policy.push("upgrade-insecure-requests");
  }
  return policy.join("; ");
}
