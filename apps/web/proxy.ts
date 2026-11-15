import { NextResponse, type NextRequest } from "next/server";
import { getPublicConfig } from "@oldpages/config";
import { buildCsp } from "./lib/csp";

// A fresh nonce per request. Next.js reads it from the request's CSP header and adds it to
// its own <script> tags, so they run while any injected script is refused.
export function proxy(request: NextRequest) {
  const nonce = btoa(crypto.randomUUID());
  const csp = buildCsp(nonce, {
    apiBaseUrl: getPublicConfig().apiBaseUrl, // the address lib/api calls
    mediaBaseUrl: process.env.NEXT_PUBLIC_MEDIA_BASE_URL,
    development: process.env.NODE_ENV === "development",
  });

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    {
      // Pages only: static files and prefetches don't execute as documents.
      source:
        "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|webp|ico)$).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
