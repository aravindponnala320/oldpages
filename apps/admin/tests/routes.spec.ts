import { expect, test } from "@playwright/test";

const now = new Date("2026-06-26T12:00:00.000Z").toISOString();

const moderationCase = {
  actions: [],
  assigned_moderator_user_id: null,
  created_at: now,
  evidence_snapshot: {},
  id: "case_1",
  priority_score: 25,
  report: {
    case_id: "case_1",
    created_at: now,
    description: "Reported listing looks suspicious.",
    evidence: {},
    id: "report_1",
    reason: "spam",
    reporter: { id: "user_1" },
    severity: "medium",
    status: "open",
    target: { id: "listing_1", type: "listing" },
  },
  severity: "medium",
  status: "open",
  summary: "Reported listing looks suspicious.",
};

const routes = [
  "/",
  "/analytics",
  "/communities",
  "/listings",
  "/login",
  "/moderation",
  "/payments",
  "/reports",
  "/reports/case_1",
  "/users",
  "/users/user_1",
];

test.describe("admin routes", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      const payload = window.btoa(JSON.stringify({ email: "admin@example.com" }));
      window.localStorage.setItem("op_access_token", `header.${payload}.signature`);
    });
  });

  for (const path of routes) {
    test(`${path} renders without unsupported API calls`, async ({ page }) => {
      const unexpectedApiCalls: string[] = [];
      const pageErrors: string[] = [];

      page.on("pageerror", (error) => pageErrors.push(error.message));

      await page.route("**/api/v1/**", async (route) => {
        const requestUrl = new URL(route.request().url());
        const pathname = requestUrl.pathname;

        if (pathname === "/api/v1/admin/moderation/cases") {
          await route.fulfill({ json: { items: [moderationCase], next_cursor: null } });
          return;
        }

        if (pathname === "/api/v1/admin/moderation/cases/case_1") {
          await route.fulfill({ json: moderationCase });
          return;
        }

        if (pathname === "/api/v1/admin/moderation/users/user_1") {
          await route.fulfill({
            json: {
              email: "admin-target@example.com",
              id: "user_1",
              report_count: 1,
              status: "active",
            },
          });
          return;
        }

        if (pathname === "/api/v1/orders") {
          await route.fulfill({ json: { items: [], next_cursor: null } });
          return;
        }

        unexpectedApiCalls.push(pathname);
        await route.fulfill({ json: { detail: "Unexpected API call in route crawl" }, status: 404 });
      });

      await page.goto(path);
      await page.waitForLoadState("networkidle");

      await expect(page.locator("body")).not.toContainText("API error");
      await expect(page.getByRole("heading").first()).toBeVisible();
      expect(unexpectedApiCalls).toEqual([]);
      expect(pageErrors).toEqual([]);
    });
  }
});
