import { test, expect } from "@playwright/test";
import {
  authenticatePage,
  expectRuntimeClean,
  expectUsablePage,
  jsonRequest,
  loginByApi,
  observeRuntime,
} from "./support.mjs";

const projectId = "PRJ-FRONTEND-ROLE-AUDIT";
const readableSections = [
  ["", "Kiểm thử giao diện theo vai trò"],
  ["yeu-cau", "Yêu cầu"],
  ["thiet-ke-kiem-thu", "Thiết kế kiểm thử"],
  ["truy-vet", "Truy vết"],
  ["thay-doi", "Phân tích thay đổi"],
  ["thuc-thi", "Thực thi kiểm thử"],
  ["ra-soat-ai", "Rà soát đề xuất AI"],
  ["loi", "Lỗi"],
  ["bao-cao", "Báo cáo"],
  ["tri-thuc", "Kho tri thức"],
];

const textDocument = (text) => ({
  type: "doc",
  content: [{ type: "paragraph", content: [{ type: "text", text }] }],
});

async function openSection(page, path, heading) {
  await page.goto(path);
  await page
    .getByRole("heading", { level: 1, name: heading })
    .waitFor({ state: "visible", timeout: 15000 });
}

for (const role of ["lead", "tester", "ba", "developer", "viewer"]) {
  test(`${role} mở được toàn bộ khu vực có quyền đọc`, async ({ page, request }) => {
    test.setTimeout(180000);
    const errors = observeRuntime(page);
    const token = await loginByApi(request, role);
    const response = await request.get(`http://localhost:8000/kiem-thu/du-an/${projectId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const project = (await response.json()).data;
    expect(project.current_membership.project_role).toBe(
      { lead: "QA_LEAD", tester: "TESTER", ba: "BA", developer: "DEVELOPER", viewer: "VIEWER" }[
        role
      ],
    );
    await authenticatePage(page, request, role);
    await openSection(page, "/du-an", "Dự án");
    await expectUsablePage(page);
    await openSection(page, "/cai-dat", "Tài khoản và bảo mật");
    await expectUsablePage(page);
    await openSection(page, "/thong-bao", "Thông báo");
    await expectUsablePage(page);
    for (const [section, heading] of readableSections) {
      await openSection(page, `/du-an/${projectId}${section ? `/${section}` : ""}`, heading);
      await expectUsablePage(page);
      const permissionButtons = {
        "yeu-cau": [
          ["Tạo yêu cầu", "requirement.create"],
          ["Nhập tài liệu", "requirement_document.upload"],
        ],
        "thiet-ke-kiem-thu": [["Tạo ca kiểm thử", "testcase.create"]],
        "thuc-thi": [
          ["Tạo kế hoạch", "testplan.create"],
          ["Tạo bộ kiểm thử", "testsuite.create"],
          ["Tạo lần chạy", "testrun.create"],
        ],
        loi: [["Tạo lỗi", "defect.create"]],
        "tri-thuc": [["Thêm nguồn tri thức", "knowledge.manage"]],
      };
      for (const [label, permission] of permissionButtons[section] || []) {
        await expect(page.getByRole("button", { name: label, exact: true })).toHaveCount(
          project.current_permissions.includes(permission) ? 1 : 0,
        );
      }
    }
    await page.goto(`/du-an/${projectId}/cai-dat`);
    if (role === "lead") {
      await expect(
        page.getByRole("heading", { level: 1, name: "Cài đặt và nhật ký" }),
      ).toBeVisible();
    } else {
      await expect(page.getByText("Bạn không có quyền mở khu vực này trong dự án")).toBeVisible();
    }
    await expectRuntimeClean(errors);
  });
}

test("admin mở được toàn bộ khu vực quản trị đã nối với backend", async ({ page, request }) => {
  test.setTimeout(180000);
  const errors = observeRuntime(page);
  await authenticatePage(page, request, "admin");
  await openSection(page, "/du-an", "Dự án");
  await expectUsablePage(page);
  await openSection(page, "/cai-dat", "Tài khoản và bảo mật");
  await expectUsablePage(page);
  await openSection(page, "/thong-bao", "Thông báo");
  await expectUsablePage(page);
  await openSection(page, "/van-hanh", "Vận hành nền tảng");
  await expectUsablePage(page);
  await page.getByRole("button", { name: "Tài khoản", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Tài khoản hệ thống" })).toBeVisible();
  await expect(page.getByText("Người dùng", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Cấu hình nền tảng", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Trạng thái dịch vụ nền tảng" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Cấu hình nền tảng" })).toBeVisible();
  await expect(page.getByText("Not Found", { exact: true })).toHaveCount(0);
  await expect(page.getByText("UNKNOWN", { exact: true })).toHaveCount(0);
  await expectUsablePage(page);
  await expectRuntimeClean(errors);
});

test("người xem dùng được giao diện dự án trên màn hình hẹp", async ({ page, request }) => {
  const errors = observeRuntime(page);
  await page.setViewportSize({ width: 320, height: 720 });
  await authenticatePage(page, request, "viewer");
  await page.goto(`/du-an/${projectId}`);
  await expect(
    page.getByRole("heading", { level: 1, name: "Kiểm thử giao diện theo vai trò" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth - innerWidth),
  ).toBeLessThanOrEqual(1);
  await page.getByRole("button", { name: "Mở điều hướng" }).click();
  await expect(page.getByRole("link", { name: "Cài đặt và nhật ký" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Vận hành nền tảng" })).toHaveCount(0);
  await expectRuntimeClean(errors);
});

test("các lỗi thao tác thủ công trong Fix docx không tái diễn", async ({ page, request }) => {
  test.setTimeout(180000);
  const errors = observeRuntime(page);
  const leadToken = await loginByApi(request, "lead");
  const testerToken = await loginByApi(request, "tester");
  const stamp = Date.now();
  const title = `Yêu cầu chờ duyệt ${stamp}`;
  const createdBody = await jsonRequest(
    request,
    "POST",
    `/kiem-thu/du-an/${projectId}/yeu-cau`,
    leadToken,
    {
      requirement_key: `REQ-MANUAL-${stamp}`,
      title,
      type: "functional",
      priority: "high",
      risk: "high",
      content_doc: textDocument(
        "Khi người dùng lưu bản nháp thì hệ thống phải lưu tiêu chí chấp nhận đã cập nhật",
      ),
      acceptance_criteria: [
        { key: "AC-1", content_doc: textDocument("Tiêu chí ban đầu"), status: "draft" },
      ],
      business_rules: [],
      actors: ["Người dùng"],
      dependencies: [],
      source_refs: [],
    },
  );
  const requirement = createdBody.data;

  await authenticatePage(page, request, "lead");
  await page.goto(`/du-an/${projectId}/yeu-cau/${requirement._id}`);
  await expect(page.getByRole("heading", { level: 1, name: new RegExp(title) })).toBeVisible();
  const saveResponse = page.waitForResponse(
    (response) =>
      response.url().includes(`/cong-tac/yeu-cau/${requirement._id}/thao-tac`) &&
      response.request().method() === "POST",
  );
  await page.getByLabel("Tiêu chí chấp nhận").fill("Tiêu chí đã sửa\nTiêu chí thứ hai");
  await page.getByRole("button", { name: "Lưu bản nháp", exact: true }).click();
  expect((await saveResponse).ok()).toBeTruthy();
  await expect(page.getByText("Đã tự động lưu", { exact: true })).toBeVisible();

  const savedBody = await jsonRequest(
    request,
    "GET",
    `/kiem-thu/yeu-cau/${requirement._id}`,
    leadToken,
  );
  expect(savedBody.data.current_version.acceptance_criteria).toHaveLength(2);

  await authenticatePage(page, request, "tester");
  await page.goto(`/du-an/${projectId}/thiet-ke-kiem-thu`);
  await expect(page.getByRole("heading", { level: 1, name: "Thiết kế kiểm thử" })).toBeVisible();
  await expect(page.getByRole("option", { name: new RegExp(title) })).toHaveCount(0);

  const submittedBody = await jsonRequest(
    request,
    "POST",
    `/kiem-thu/du-an/${projectId}/yeu-cau/${requirement._id}/gui-ra-soat`,
    leadToken,
    {
      expected_revision: savedBody.data.current_version.revision,
      review_note: "Kiểm tra cổng rà soát",
    },
  );
  await jsonRequest(
    request,
    "POST",
    `/kiem-thu/phien-ban-yeu-cau/${requirement.current_version._id}/chot-chuan`,
    leadToken,
    { expected_revision: submittedBody.data.revision },
  );
  await page.reload();
  await expect(page.getByRole("option", { name: new RegExp(title) }).first()).toBeAttached();

  await authenticatePage(page, request, "ba");
  await page.goto(`/du-an/${projectId}/thiet-ke-kiem-thu`);
  await expect(page.getByRole("heading", { level: 1, name: "Thiết kế kiểm thử" })).toBeVisible();
  await expect(page.getByText("PROJECT_PERMISSION_DENIED", { exact: true })).toHaveCount(0);
  await expectUsablePage(page);

  await page.setViewportSize({ width: 1366, height: 900 });
  await authenticatePage(page, request, "lead");
  await page.goto(`/du-an/${projectId}/cai-dat`);
  await expect(page.getByRole("heading", { level: 2, name: "Thành viên dự án" })).toBeVisible();
  await expect(page.getByText("ACTIVE", { exact: true })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Vô hiệu hóa", exact: true }).first(),
  ).toBeVisible();
  await expectUsablePage(page);
  await expectRuntimeClean(errors);
});
