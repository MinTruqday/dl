import { expect } from "@playwright/test";

const tokens = new Map();

export const credentials = {
  lead: {
    email: "e2e-qa-lead@example.com",
    password: "Veriq-E2E-Password-2026",
  },
  tester: {
    email: "e2e-tester@example.com",
    password: "Veriq-E2E-Password-2026",
  },
  ba: {
    email: "e2e-ba@example.com",
    password: "Veriq-E2E-Password-2026",
  },
  developer: {
    email: "e2e-developer@example.com",
    password: "Veriq-E2E-Password-2026",
  },
  viewer: {
    email: "e2e-viewer@example.com",
    password: "Veriq-E2E-Password-2026",
  },
  admin: {
    email: "e2e-admin@example.com",
    password: "Veriq-E2E-Password-2026",
  },
};

export function observeRuntime(page) {
  const errors = [];
  page.on("pageerror", (error) => errors.push(`pageerror ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource")) {
      errors.push(`console ${message.text()}`);
    }
  });
  page.on("requestfailed", (request) => {
    const failure = request.failure();
    const url = request.url();
    if (!url.includes("_next/webpack-hmr") && !failure?.errorText?.includes("ERR_ABORTED")) {
      errors.push(`requestfailed ${request.method()} ${url} ${failure?.errorText || "unknown"}`);
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 500) {
      errors.push(`response ${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });
  return errors;
}

export async function expectRuntimeClean(errors) {
  await expect.poll(() => errors, { timeout: 1000 }).toEqual([]);
}

export async function loginByApi(request, role) {
  if (tokens.has(role)) return tokens.get(role);
  const account = credentials[role];
  const response = await request.post("http://localhost:8000/xac-thuc/dang-nhap", {
    form: { username: account.email, password: account.password },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const body = await response.json();
  const token = body.data.access_token;
  tokens.set(role, token);
  return token;
}

export async function authenticatePage(page, request, role) {
  const token = await loginByApi(request, role);
  await page.context().addCookies([
    { name: "token", value: token, url: "http://localhost:3000", sameSite: "Lax" },
    { name: "role", value: role, url: "http://localhost:3000" },
  ]);
  await page.addInitScript((value) => localStorage.setItem("veriq_token", value), token);
  return token;
}

export function userIdFromToken(token) {
  const encoded = token.split(".")[1];
  const normalized = encoded.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
  const payload = JSON.parse(Buffer.from(padded, "base64").toString("utf8"));
  return payload.uid;
}

export async function jsonRequest(request, method, path, token, data) {
  const response = await request.fetch(`http://localhost:8000${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    data,
  });
  const text = await response.text();
  expect(response.ok(), `${method} ${path} ${response.status()} ${text}`).toBeTruthy();
  return text ? JSON.parse(text) : null;
}

export async function expectUsablePage(page) {
  await expect(page.locator("#main-content, body > main").first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Application error");
  await expect(page.locator("body")).not.toContainText("Internal Server Error");
  await expect(page.locator("body")).not.toContainText("Failed to fetch");
  await expect(page.getByText("Not Found", { exact: true })).toHaveCount(0);
  const audit = await page.evaluate(() => {
    const duplicateIds = [...document.querySelectorAll("[id]")]
      .map((element) => element.id)
      .filter((id, index, ids) => ids.indexOf(id) !== index);
    const unlabeledInputs = [...document.querySelectorAll("input, select, textarea")]
      .filter((element) => element.type !== "hidden")
      .filter((element) => {
        const labels = element.labels ? [...element.labels] : [];
        return (
          !labels.length &&
          !element.getAttribute("aria-label") &&
          !element.getAttribute("aria-labelledby")
        );
      })
      .map((element) => element.outerHTML.slice(0, 180));
    const unnamedButtons = [...document.querySelectorAll("button")]
      .filter(
        (button) =>
          !button.textContent.trim() &&
          !button.getAttribute("aria-label") &&
          !button.getAttribute("aria-labelledby"),
      )
      .map((button) => button.outerHTML.slice(0, 180));
    const horizontalOverflow = Math.max(
      document.documentElement.scrollWidth - window.innerWidth,
      document.body.scrollWidth - window.innerWidth,
    );
    return { duplicateIds, unlabeledInputs, unnamedButtons, horizontalOverflow };
  });
  expect(audit).toEqual({
    duplicateIds: [],
    unlabeledInputs: [],
    unnamedButtons: [],
    horizontalOverflow: 0,
  });
}
