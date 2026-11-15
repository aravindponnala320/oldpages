import { expect, test } from "@playwright/test";

test("home page loads", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Nearby Books" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /All books/ })).toHaveAttribute(
    "href",
    "/search",
  );
});

test("sign-in and password reset pages load", async ({ page }) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Forgot password?" }).click();
  await expect(
    page.getByRole("heading", { name: "Forgot password?" }),
  ).toBeVisible();
});

test("pages run under the Content-Security-Policy without violations", async ({
  page,
}) => {
  const violations: string[] = [];
  page.on("console", (message) => {
    if (/Content Security Policy/i.test(message.text()))
      violations.push(message.text());
  });
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (event) => {
      console.error(
        `Content Security Policy: ${event.violatedDirective} ${event.blockedURI}`,
      );
    });
  });

  const response = await page.goto("/login");
  const csp = response?.headers()["content-security-policy"] ?? "";
  expect(csp).toContain("'strict-dynamic'");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");

  // The toggle only works once React has hydrated, i.e. Next's nonced scripts ran.
  const password = page.locator('input[autocomplete="current-password"]');
  await page.getByRole("button", { name: "Show" }).click();
  await expect(password).toHaveAttribute("type", "text");

  await page.goto("/search");
  await page.goto("/");
  expect(violations).toEqual([]);
});
