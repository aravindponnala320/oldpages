import { describe, expect, it } from "vitest";

import { buildCsp } from "../lib/csp";

function directives(policy: string): Record<string, string[]> {
  return Object.fromEntries(
    policy.split("; ").map((part) => {
      const [name, ...values] = part.split(" ");
      return [name, values];
    }),
  );
}

describe("buildCsp", () => {
  it("only runs scripts that carry the request's nonce in production", () => {
    const csp = directives(
      buildCsp("abc123", {
        apiBaseUrl: "https://oldpages-api.fly.dev/",
        mediaBaseUrl: "https://media.oldpages.in/oldpages-media/x.jpg",
        development: false,
      }),
    );

    expect(csp["script-src"]).toContain("'nonce-abc123'");
    expect(csp["script-src"]).toContain("'strict-dynamic'");
    expect(csp["script-src"]).not.toContain("'unsafe-inline'");
    expect(csp["script-src"]).not.toContain("'unsafe-eval'");
    expect(csp["connect-src"]).toEqual([
      "'self'",
      "https://accounts.google.com",
      "https://oldpages-api.fly.dev",
      "wss://oldpages-api.fly.dev",
      "https://media.oldpages.in",
    ]);
    expect(csp["frame-ancestors"]).toEqual(["'none'"]);
    expect(csp["object-src"]).toEqual(["'none'"]);
    expect(csp["upgrade-insecure-requests"]).toEqual([]);
  });

  it("keeps uploads working when the bucket address isn't configured", () => {
    const csp = directives(
      buildCsp("n", { apiBaseUrl: "https://api.test", development: false }),
    );
    expect(csp["connect-src"]).toContain("https:");
  });

  it("doesn't force https for a local production build", () => {
    const csp = directives(
      buildCsp("n", {
        apiBaseUrl: "http://localhost:8000",
        development: false,
      }),
    );
    expect(csp["connect-src"]).toContain("http://localhost:8000");
    expect(csp["upgrade-insecure-requests"]).toBeUndefined();
  });

  it("allows the dev server's eval and local sockets only in development", () => {
    const csp = directives(
      buildCsp("n", {
        apiBaseUrl: "http://localhost:8000",
        mediaBaseUrl: "http://localhost:9000",
        development: true,
      }),
    );
    expect(csp["script-src"]).toContain("'unsafe-eval'");
    expect(csp["connect-src"]).toContain("ws://localhost:8000");
    expect(csp["img-src"]).toContain("http://localhost:9000");
    expect(csp["upgrade-insecure-requests"]).toBeUndefined();
  });
});
