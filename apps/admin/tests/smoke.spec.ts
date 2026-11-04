import { expect, test } from "@playwright/test";

test("admin shell loads", async ({ page }) => {
  await page.addInitScript(() => {
    const payload = window.btoa(JSON.stringify({ email: "admin@example.com" }));
    window.localStorage.setItem("op_access_token", `header.${payload}.signature`);
  });

  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Dashboard" }),
  ).toBeVisible();
});
