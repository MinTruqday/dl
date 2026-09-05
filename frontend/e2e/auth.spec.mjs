import { test, expect } from "@playwright/test";
import { credentials, expectRuntimeClean, observeRuntime } from "./support.mjs";

test("trang chủ giới thiệu sản phẩm rõ ràng và không tràn trên thiết bị di động", async ({
  page,
}) => {
  const errors = observeRuntime(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Quản lý kiểm thử phần mềm" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Tạo tài khoản" })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
  ).toBeLessThanOrEqual(1);
  await expectRuntimeClean(errors);
});

test("đăng nhập báo đúng lỗi và đăng nhập người dùng thành công", async ({ page }) => {
  const errors = observeRuntime(page);
  await page.goto("/dang-nhap");
  await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  await page.getByLabel("Email").fill(credentials.lead.email);
  await page.locator("#login-password").fill("MatKhauKhongDung-2026");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByText("Không thể đăng nhập")).toBeVisible();
  await page.locator("#login-password").fill(credentials.lead.password);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/du-an$/);
  await expect(page.getByRole("heading", { name: "Dự án kiểm thử" })).toBeVisible();
  await expectRuntimeClean(errors);
});

test("passkey yêu cầu email trước khi thao tác", async ({ page }) => {
  const errors = observeRuntime(page);
  await page.goto("/dang-nhap");
  await page.getByRole("button", { name: "Passkey" }).click();
  await expect(page.getByText("Nhập email trước khi dùng Passkey")).toBeVisible();
  await expectRuntimeClean(errors);
});

test("đăng ký kiểm tra điều khoản và tạo tài khoản thật", async ({ page }) => {
  const errors = observeRuntime(page);
  const unique = Date.now();
  await page.goto("/dang-ky");
  await page.getByLabel("Tên hiển thị").fill("Người dùng kiểm thử");
  await page.getByLabel("Tên tài khoản").fill(`e2e_${unique}`);
  await page.getByLabel("Email").fill(`e2e-${unique}@example.com`);
  await page.locator("#register-password").fill("Registration-Password-2026");
  await page.getByRole("button", { name: "Tạo tài khoản" }).click();
  await expect(page.getByText("Cần chấp thuận điều khoản để tạo tài khoản")).toBeVisible();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Tạo tài khoản" }).click();
  await expect(page).toHaveURL(/\/dang-nhap$/);
  await expectRuntimeClean(errors);
});

test("các màn hình khôi phục và điều khoản hiển thị được", async ({ page }) => {
  const errors = observeRuntime(page);
  for (const path of ["/quen-mat-khau", "/xac-thuc", "/dat-lai-mat-khau", "/dieu-khoan"]) {
    await page.goto(path);
    await expect(page.locator("body")).not.toContainText("Application error");
  }
  await expectRuntimeClean(errors);
});
