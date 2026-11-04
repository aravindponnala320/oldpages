import { expect, test } from "@playwright/test";

test("web shell loads", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Buy, sell, and exchange books near you" }),
  ).toBeVisible();
});
