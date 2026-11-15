import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("API addresses", () => {
  it("opens chat sockets on the API host, not the web host", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.oldpages.in/");
    const { apiBaseUrl, socketBaseUrl } = await import("../lib/api");
    expect(socketBaseUrl).toBe("wss://api.oldpages.in");
    expect(`${apiBaseUrl}/api/v1/listings`).toBe(
      "https://api.oldpages.in/api/v1/listings",
    );
  });

  it("uses plain ws for a local http API", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000");
    const { socketBaseUrl } = await import("../lib/api");
    expect(socketBaseUrl).toBe("ws://localhost:8000");
  });
});
