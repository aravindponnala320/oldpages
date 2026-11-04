import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import HomePage from "../app/page";

vi.mock("../lib/api", () => ({
  apiClient: {
    listCategories: vi.fn().mockResolvedValue({ items: [] }),
    searchListings: vi.fn().mockResolvedValue({ items: [] }),
  },
}));

describe("HomePage", () => {
  it("renders the marketplace landing flow", async () => {
    render(await HomePage());

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Buy, sell, and exchange books near you",
      }),
    ).toBeDefined();
    expect(screen.getByRole("heading", { name: "Recent Listings" })).toBeDefined();
    expect(screen.getByRole("heading", { name: "How it works" })).toBeDefined();
  });
});
