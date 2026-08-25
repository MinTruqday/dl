import { test, expect } from "@playwright/test";
import {
  authenticatePage,
  expectRuntimeClean,
  expectUsablePage,
  loginByApi,
  observeRuntime,
} from "./support.mjs";

const doc = (text) => ({
  type: "doc",
  content: [{ type: "paragraph", content: [{ type: "text", text }] }],
});

async function qa(request, token, method, path, data, expected = 200) {
  const response = await request.fetch(`http://localhost:8000/api/qa${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    data,
  });
  const text = await response.text();
  expect(response.status(), `${method} ${path} ${text}`).toBe(expected);
  const body = JSON.parse(text);
  expect(body.meta?.trace_id).toBeTruthy();
  return body.data;
}

async function createBoundaryTest(request, token, projectId, requirementVersion, value, accepted) {
  const key = `TC-PROFILE-0${value === 9 ? 41 : value === 10 ? 42 : 43}`;
  const draft = await qa(
    request,
    token,
    "POST",
    `/projects/${projectId}/test-case-drafts`,
    {
      test_case_key: key,
      title: `Số điện thoại ${value} chữ số ${accepted ? "được chấp nhận" : "bị từ chối"}`,
      type: "boundary",
      priority: "high",
      risk: "high",
      preconditions_doc: doc("Người dùng đang chỉnh sửa hồ sơ"),
      steps: [
        {
          id: "step-1",
          order: 1,
          action_doc: doc(`Nhập số điện thoại gồm ${value} chữ số`),
          test_data: { length: value },
          expected_doc: doc(accepted ? "Hệ thống chấp nhận" : "Hệ thống từ chối"),
        },
      ],
      test_data: { length: value },
      expected_result_doc: doc(accepted ? "Hệ thống chấp nhận" : "Hệ thống từ chối"),
      postconditions_doc: doc("Hồ sơ được kiểm soát"),
      requirement_version_ids: [requirementVersion._id],
      acceptance_criterion_ids: requirementVersion.acceptance_criterion_ids,
      origin: "manual",
    },
    201,
  );
  const frozen = await qa(
    request,
    token,
    "POST",
    `/test-case-drafts/${draft._id}/freeze`,
    { expected_revision: 1, change_reason: "Phê duyệt kịch bản biên" },
    201,
  );
  return frozen;
}

test("luồng chữ ký Requirement đến Regression bảo toàn phiên bản và quyết định con người", async ({
  page,
  request,
}) => {
  test.setTimeout(180000);
  const errors = observeRuntime(page);
  const token = await loginByApi(request, "teacher");
  await authenticatePage(page, request, "teacher");
  const stamp = Date.now();
  const project = await qa(
    request,
    token,
    "POST",
    "/projects",
    {
      key: `SIG${stamp}`,
      name: `Phone Signature ${stamp}`,
      description: "Kịch bản chữ ký V1",
      project_type: "web",
      settings: {},
    },
    201,
  );
  const requirement = await qa(
    request,
    token,
    "POST",
    `/projects/${project._id}/requirements`,
    {
      requirement_key: "REQ-PROFILE-004",
      title: "Giới hạn số điện thoại",
      type: "functional",
      priority: "high",
      risk: "high",
      content_doc: doc("Khi người dùng nhập Phone thì hệ thống chỉ cho phép exactly 10 digits"),
      acceptance_criteria: [
        { key: "AC-01", content_doc: doc("Phone có đúng 10 chữ số thì chấp nhận") },
      ],
      business_rules: [],
      actors: ["User"],
      dependencies: [],
      source_refs: [],
    },
    201,
  );
  const v1 = await qa(
    request,
    token,
    "POST",
    `/requirement-versions/${requirement.current_version._id}/baseline`,
    { expected_revision: 1 },
  );
  const tc41 = await createBoundaryTest(request, token, project._id, v1, 9, false);
  const tc42 = await createBoundaryTest(request, token, project._id, v1, 10, true);
  const tc43 = await createBoundaryTest(request, token, project._id, v1, 11, false);
  const plan = await qa(
    request,
    token,
    "POST",
    "/test-plans",
    {
      project_id: project._id,
      name: "Phone Plan",
      objective: "Xác minh biên",
      scope_in: ["Profile"],
      scope_out: [],
      environment: "staging",
      entry_criteria: [],
      exit_criteria: [],
      risks: [],
      test_types: ["boundary"],
      members: [],
      release: "v1",
      build: "1.0.0",
    },
    201,
  );
  const run = await qa(
    request,
    token,
    "POST",
    "/test-runs",
    {
      project_id: project._id,
      name: "Phone Run v1",
      test_plan_id: plan._id,
      test_suite_ids: [],
      test_case_version_ids: [tc41.version._id, tc42.version._id, tc43.version._id],
      environment: "staging",
      build: "1.0.0",
    },
    201,
  );
  await qa(request, token, "POST", `/test-runs/${run._id}/start`);
  for (const version of [tc41.version, tc42.version, tc43.version])
    await qa(request, token, "POST", `/test-runs/${run._id}/results/${version._id}`, {
      status: "PASS",
      step_results: [],
      attachments: [],
      note: "Manual execution",
      idempotency_key: crypto.randomUUID(),
    });
  await qa(request, token, "POST", `/test-runs/${run._id}/complete`);
  const v2Draft = await qa(
    request,
    token,
    "POST",
    `/requirements/${requirement._id}/versions`,
    {
      requirement_key: "REQ-PROFILE-004",
      title: "Giới hạn số điện thoại",
      type: "functional",
      priority: "high",
      risk: "high",
      content_doc: doc("Khi người dùng nhập Phone thì hệ thống cho phép 10 or 11 digits"),
      acceptance_criteria: [
        { key: "AC-01", content_doc: doc("Phone có 10 hoặc 11 chữ số thì chấp nhận") },
      ],
      business_rules: [],
      actors: ["User"],
      dependencies: [],
      source_refs: [],
      change_reason: "Mở rộng biên",
      expected_current_version_id: v1._id,
    },
    201,
  );
  const v2 = await qa(request, token, "POST", `/requirement-versions/${v2Draft._id}/baseline`, {
    expected_revision: 1,
  });
  const change = await qa(
    request,
    token,
    "POST",
    `/requirements/${requirement._id}/change-sets`,
    { from_version_id: v1._id, to_version_id: v2._id },
    201,
  );
  expect(change.changes[0]).toMatchObject({
    type: "MODIFIED_BOUNDARY",
    before: { values: [10] },
    after: { values: [10, 11] },
  });
  const impact = await qa(
    request,
    token,
    "POST",
    `/change-sets/${change._id}/impact-analysis`,
    undefined,
    201,
  );
  const byKey = Object.fromEntries(
    impact.affected_test_cases.map((item) => [item.test_case_key, item.classification]),
  );
  expect(byKey).toMatchObject({
    "TC-PROFILE-041": "STILL_VALID",
    "TC-PROFILE-042": "STILL_VALID",
    "TC-PROFILE-043": "NEEDS_UPDATE",
  });
  const proposals = await qa(
    request,
    token,
    "POST",
    `/impact-analyses/${impact._id}/maintenance-proposals`,
    undefined,
    201,
  );
  const proposal = proposals.find((item) => item.test_case_key === "TC-PROFILE-043");
  const applied = await qa(
    request,
    token,
    "POST",
    `/maintenance-proposals/${proposal._id}/accept-with-edit`,
    {
      expected_revision: proposal.revision,
      patch: { expected_result_doc: doc("Hệ thống chấp nhận số điện thoại 11 chữ số") },
      review_note: "Tester xác nhận evidence",
    },
    201,
  );
  expect(applied.result.version).toBe(2);
  const history = await qa(request, token, "GET", `/test-cases/${tc43.test_case._id}/versions`);
  expect(history.map((item) => item.version)).toEqual([2, 1]);
  const runSnapshot = await qa(request, token, "GET", `/test-runs/${run._id}`);
  expect(runSnapshot.test_case_version_ids).toContain(tc43.version._id);
  expect(runSnapshot.test_case_version_ids).not.toContain(applied.result._id);
  const regression = await qa(
    request,
    token,
    "POST",
    `/change-sets/${change._id}/regression-recommendation`,
    undefined,
    201,
  );
  expect(regression.items).toHaveLength(3);
  expect(regression.items.every((item) => item.level === "MUST_RUN")).toBeTruthy();
  expect(
    regression.items.find((item) => item.test_case_key === "TC-PROFILE-043").test_case_version_id,
  ).toBe(applied.result._id);
  await page.goto(`/qa/projects/${project._id}`);
  await expect(page.getByRole("heading", { level: 1, name: project.name })).toBeVisible();
  await expect(page.getByText("100%", { exact: true }).first()).toBeVisible();
  for (const [path, heading] of [
    ["requirements", "Yêu cầu và phiên bản chuẩn"],
    ["test-design", "Kịch bản và ca kiểm thử"],
    ["traceability", "Ma trận truy vết và độ phủ"],
    ["changes", "Ảnh hưởng thay đổi và bảo trì"],
    ["execution", "Kế hoạch, bộ kiểm thử và lần chạy"],
    ["defects", "Quản lý lỗi"],
    ["knowledge", "Tìm kiếm trong tri thức dự án"],
    ["settings", "Cài đặt và kiểm toán"],
  ]) {
    await page.goto(`/qa/projects/${project._id}/${path}`);
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    if (path === "test-design") {
      const toolbar = page.getByRole("toolbar", { name: "Công cụ soạn thảo QA" }).first();
      await expect(toolbar).toBeVisible();
      for (const name of [
        "Đánh dấu",
        "Chỉ số dưới",
        "Chỉ số trên",
        "Danh sách tác vụ",
        "Căn giữa",
        "Màu chữ",
        "Phông chữ",
        "Công thức",
        "Khối thu gọn",
        "Chèn bảng",
      ]) {
        await expect(toolbar.getByLabel(name, { exact: true })).toBeVisible();
      }
      const actionEditor = page.getByRole("textbox", { name: "Thao tác của ca kiểm thử" });
      await actionEditor.click();
      await toolbar.getByRole("button", { name: "In đậm" }).click();
      await actionEditor.pressSequentially("Nội dung in đậm");
      await expect(actionEditor.locator("strong")).toHaveText("Nội dung in đậm");
      await expect(toolbar.getByText(/\d+ ký tự/)).toBeVisible();
    }
    await expectUsablePage(page);
  }
  await page.goto("/cai-dat");
  await expect(page.getByRole("heading", { level: 1, name: "Tài khoản và bảo mật" })).toBeVisible();
  await expectUsablePage(page);
  await expectRuntimeClean(errors);
});

test("người dùng tạo dự án bằng frontend thật và giao diện di động không tràn ngang", async ({
  page,
  request,
}) => {
  const errors = observeRuntime(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await authenticatePage(page, request, "teacher");
  await page.goto("/qa/projects");
  await page.getByRole("button", { name: "Tạo dự án" }).click();
  const stamp = Date.now();
  await page.getByLabel("Mã dự án").fill(`UI${stamp}`);
  await page.getByLabel("Tên dự án").fill(`Dự án giao diện ${stamp}`);
  await page.getByRole("button", { name: "Lưu dự án" }).click();
  await expect(page.getByText(`Dự án giao diện ${stamp}`)).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth),
  ).toBeLessThanOrEqual(1);
  await expectRuntimeClean(errors);
});
