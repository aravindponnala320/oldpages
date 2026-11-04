import { createElement } from "react";
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AdminPage from "../app/page";

describe("AdminPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = input.toString();
        if (url.includes("/admin/moderation/cases")) {
          return Response.json({ items: [] });
        }
        return Response.json({}, { status: 404 });
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the operations dashboard", async () => {
    render(createElement(AdminPage));

    expect(screen.getByRole("heading", { level: 1, name: "Dashboard" })).toBeDefined();
    expect(await screen.findByText("Total Users")).toBeDefined();
    expect(screen.getByText("Active Listings")).toBeDefined();
    expect(screen.getByText("Recent Moderation Activity")).toBeDefined();
  });
});
