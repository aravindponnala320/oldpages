import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../app/page";
import { apiClient } from "../lib/api";

const cookieJar = new Map<string, string>();

vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: (name: string) =>
      cookieJar.has(name) ? { name, value: cookieJar.get(name) } : undefined,
  }),
}));

vi.mock("../lib/api", () => ({
  apiClient: {
    searchListings: vi.fn().mockResolvedValue({ items: [] }),
  },
}));

describe("HomePage", () => {
  beforeEach(() => {
    cookieJar.clear();
    vi.mocked(apiClient.searchListings).mockClear();
  });

  it("shows the category shortcuts and the nearby section", async () => {
    render(await HomePage());

    expect(screen.getByRole("heading", { name: "Nearby Books" })).toBeDefined();
    expect(
      screen.getByText("Set your location above to see nearby books"),
    ).toBeDefined();
    expect(
      screen.getByRole("link", { name: /School/ }).getAttribute("href"),
    ).toBe("/search?category=academic.school");
    expect(
      screen.getByRole("link", { name: /All books/ }).getAttribute("href"),
    ).toBe("/search");
  });

  it("asks the API for books near the saved location", async () => {
    cookieJar.set("op_loc", "saved-location");

    render(await HomePage());

    expect(apiClient.searchListings).toHaveBeenCalledWith(
      { sort: "newest", limit: 8 },
      undefined,
      { "X-User-Location": "saved-location" },
    );
  });
});
