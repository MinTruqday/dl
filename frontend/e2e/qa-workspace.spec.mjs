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
  const response = await request.fetch(`http://localhost:8000/kiem-thu${path}`, {
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
    `/du-an/${projectId}/ban-nhap-ca-kiem-thu`,
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
  await qa(request, token, "POST", `/du-an/${projectId}/ca-kiem-thu/${draft._id}/gui-ra-soat`, {
    expected_revision: 1,
    review_note: "Đã rà soát kịch bản",
  });
  const frozen = await qa(
    request,
    token,
    "POST",
    `/ban-nhap-ca-kiem-thu/${draft._id}/dong-bang`,
    { expected_revision: 2, change_reason: "Phê duyệt kịch bản biên" },
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
  const token = await loginByApi(request, "lead");
  await authenticatePage(page, request, "lead");
  const stamp = Date.now();
  const project = await qa(
    request,
    token,
    "POST",
    "/du-an",
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
    `/du-an/${project._id}/yeu-cau`,
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
  await qa(request, token, "POST", `/du-an/${project._id}/yeu-cau/${requirement._id}/gui-ra-soat`, {
    expected_revision: 1,
    review_note: "Đã rà soát",
  });
  const v1 = await qa(
    request,
    token,
    "POST",
    `/phien-ban-yeu-cau/${requirement.current_version._id}/chot-chuan`,
    { expected_revision: 2 },
  );
  const tc41 = await createBoundaryTest(request, token, project._id, v1, 9, false);
  const tc42 = await createBoundaryTest(request, token, project._id, v1, 10, true);
  const tc43 = await createBoundaryTest(request, token, project._id, v1, 11, false);
  const plan = await qa(
    request,
    token,
    "POST",
    "/ke-hoach-kiem-thu",
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
    "/lan-chay-kiem-thu",
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
  await qa(request, token, "POST", `/lan-chay-kiem-thu/${run._id}/bat-dau`);
  for (const version of [tc41.version, tc42.version, tc43.version])
    await qa(request, token, "POST", `/lan-chay-kiem-thu/${run._id}/ket-qua/${version._id}`, {
      status: "PASS",
      step_results: (version.steps || []).map((step) => ({
        step_id: step.id,
        status: "PASS",
        actual_doc: doc("Kết quả từng bước đúng như mong đợi"),
        attachments: [],
        note: "Đã kiểm tra thủ công",
      })),
      attachments: [],
      note: "Manual execution",
      idempotency_key: crypto.randomUUID(),
    });
  await qa(request, token, "POST", `/lan-chay-kiem-thu/${run._id}/hoan-tat`);
  const v2Draft = await qa(
    request,
    token,
    "POST",
    `/yeu-cau/${requirement._id}/phien-ban`,
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
  await qa(request, token, "POST", `/du-an/${project._id}/yeu-cau/${requirement._id}/gui-ra-soat`, {
    expected_revision: 1,
    review_note: "Đã rà soát thay đổi",
  });
  const v2 = await qa(request, token, "POST", `/phien-ban-yeu-cau/${v2Draft._id}/chot-chuan`, {
    expected_revision: 2,
  });
  const change = await qa(
    request,
    token,
    "POST",
    `/yeu-cau/${requirement._id}/bo-thay-doi`,
    { from_version_id: v1._id, to_version_id: v2._id },
    201,
  );
  expect(change.changes[0]).toMatchObject({
    type: "MODIFIED_BOUNDARY",
    before: { values: [10] },
    after: { values: [10, 11] },
  });
  await qa(request, token, "POST", `/bo-thay-doi/${change._id}/ra-soat`, {
    expected_revision: 1,
    changes: change.changes,
    review_note: "Đã xác nhận ChangeFact",
  });
  const impact = await qa(
    request,
    token,
    "POST",
    `/bo-thay-doi/${change._id}/phan-tich-anh-huong`,
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
  await qa(request, token, "POST", `/phan-tich-anh-huong/${impact._id}/ra-soat`, {
    expected_revision: impact.revision,
    overrides: [],
    review_note: "Đã duyệt phân tích tác động",
  });
  const proposals = await qa(
    request,
    token,
    "POST",
    `/phan-tich-anh-huong/${impact._id}/de-xuat-bao-tri`,
    undefined,
    201,
  );
  const proposal = proposals.find((item) => item.test_case_key === "TC-PROFILE-043");
  const applied = await qa(
    request,
    token,
    "POST",
    `/de-xuat-bao-tri/${proposal._id}/chap-nhan-co-chinh-sua`,
    {
      expected_revision: proposal.revision,
      patch: { expected_result_doc: doc("Hệ thống chấp nhận số điện thoại 11 chữ số") },
      review_note: "Tester xác nhận evidence",
    },
    201,
  );
  expect(applied.result.version).toBe(2);
  const history = await qa(request, token, "GET", `/ca-kiem-thu/${tc43.test_case._id}/phien-ban`);
  expect(history.map((item) => item.version)).toEqual([2, 1]);
  const runSnapshot = await qa(request, token, "GET", `/lan-chay-kiem-thu/${run._id}`);
  expect(runSnapshot.test_case_version_ids).toContain(tc43.version._id);
  expect(runSnapshot.test_case_version_ids).not.toContain(applied.result._id);
  const regression = await qa(
    request,
    token,
    "POST",
    `/bo-thay-doi/${change._id}/de-xuat-hoi-quy`,
    undefined,
    201,
  );
  expect(regression.items).toHaveLength(3);
  expect(regression.items.every((item) => item.level === "MUST_RUN")).toBeTruthy();
  expect(
    regression.items.find((item) => item.test_case_key === "TC-PROFILE-043").test_case_version_id,
  ).toBe(applied.result._id);
  await page.goto(`/du-an/${project._id}`);
  await expect(page.getByRole("heading", { level: 1, name: project.name })).toBeVisible();
  await expect(page.getByText("100%", { exact: true }).first()).toBeVisible();
  for (const [path, heading] of [
    ["yeu-cau", "Yêu cầu"],
    ["thiet-ke-kiem-thu", "Thiết kế kiểm thử"],
    ["truy-vet", "Truy vết"],
    ["thay-doi", "Phân tích thay đổi"],
    ["thuc-thi", "Thực thi kiểm thử"],
    ["loi", "Lỗi"],
    ["tri-thuc", "Kho tri thức"],
    ["cai-dat", "Cài đặt và nhật ký"],
  ]) {
    await page.goto(`/du-an/${project._id}/${path}`);
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
    if (path === "thiet-ke-kiem-thu") {
      await page.getByRole("button", { name: "Tạo ca kiểm thử", exact: true }).click();
      await expect(page.getByRole("dialog", { name: "Tạo ca kiểm thử" })).toBeVisible();
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
  await page.goto(`/du-an/${project._id}/yeu-cau/${requirement._id}`);
  await expect(page.getByRole("heading", { name: "Nhận xét rà soát" })).toBeVisible();
  await page.getByLabel("Nội dung nhận xét").fill("Đã đối chiếu tiêu chí với nguồn nghiệp vụ");
  await page.getByRole("button", { name: "Thêm nhận xét" }).click();
  await expect(page.getByText("Đã đối chiếu tiêu chí với nguồn nghiệp vụ")).toBeVisible();
  await page.goto(`/du-an/${project._id}/thiet-ke-kiem-thu`);
  await page.getByText("TC-PROFILE-041", { exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Biên tập TC-PROFILE-041" })).toBeVisible();
  await page.getByLabel("Nội dung nhận xét").fill("Các bước và dữ liệu biên đã được rà soát");
  await page.getByRole("button", { name: "Thêm nhận xét" }).click();
  await expect(page.getByText("Các bước và dữ liệu biên đã được rà soát")).toBeVisible();
  await page.goto(`/du-an/${project._id}/truy-vet`);
  await expect(page.getByText("Độ phủ còn hiệu lực")).toBeVisible();
  await expect(page.getByText("Độ phủ thực thi")).toBeVisible();
  await page.goto(`/du-an/${project._id}/thuc-thi/${run._id}`);
  await expect(page.getByText("Đạt", { exact: true })).toHaveCount(3);
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
  await authenticatePage(page, request, "lead");
  await page.goto("/du-an");
  await expect(page.getByRole("heading", { level: 1, name: "Dự án", exact: true })).toBeVisible();
  await expect(page.getByText("Dự án kiểm thử", { exact: true })).toHaveCount(0);
  const searchInput = page.getByRole("textbox", { name: "Tìm dự án" });
  const searchIcon = searchInput.locator("xpath=preceding-sibling::*[name()='svg']");
  const alignment = await Promise.all([searchInput.boundingBox(), searchIcon.boundingBox()]);
  expect(alignment[0]).not.toBeNull();
  expect(alignment[1]).not.toBeNull();
  expect(
    Math.abs(alignment[0].y + alignment[0].height / 2 - (alignment[1].y + alignment[1].height / 2)),
  ).toBeLessThanOrEqual(1);
  await page.getByRole("button", { name: "Tạo dự án" }).click();
  const createDialog = page.getByRole("dialog", { name: "Tạo dự án" });
  await expect(createDialog).toBeVisible();
  await expect(createDialog).toBeFocused();
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

test("các nút thao tác chính tạo thay đổi thật qua backend", async ({ page, request }) => {
  test.setTimeout(120000);
  const errors = observeRuntime(page);
  const token = await loginByApi(request, "lead");
  await authenticatePage(page, request, "lead");
  const stamp = Date.now();
  const project = await qa(
    request,
    token,
    "POST",
    "/du-an",
    {
      key: `BTN${stamp}`,
      name: `Button Integration ${stamp}`,
      description: "Dự án kiểm tra thao tác giao diện",
      project_type: "web",
      settings: {},
    },
    201,
  );

  await page.goto(`/du-an/${project._id}/yeu-cau`);
  await page.getByRole("button", { name: "Tạo yêu cầu", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Tạo yêu cầu" })).toBeVisible();
  await page.getByLabel("Tên", { exact: true }).fill(`Yêu cầu giao diện ${stamp}`);
  await page.getByRole("textbox", { name: "Nội dung yêu cầu" }).fill("Nút lưu phải gọi backend");
  await page
    .getByLabel("Tiêu chí chấp nhận mỗi dòng một điều kiện")
    .fill("Yêu cầu được lưu và xuất hiện trong danh sách");
  const requirementResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/kiem-thu/du-an/${project._id}/yeu-cau`) &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Lưu yêu cầu" }).click();
  expect((await requirementResponse).status()).toBe(201);
  await expect(
    page.getByRole("cell", { name: `Yêu cầu giao diện ${stamp}`, exact: true }),
  ).toBeVisible();

  await page.goto(`/du-an/${project._id}/tri-thuc`);
  await page.getByRole("button", { name: "Thêm nguồn tri thức", exact: true }).click();
  const sourceDialog = page.getByRole("dialog", { name: "Thêm nguồn tri thức" });
  await expect(sourceDialog).toBeVisible();
  await sourceDialog.getByLabel("Tiêu đề nguồn").fill(`Nguồn giáo viên ${stamp}`);
  await sourceDialog.getByLabel("Môn học").fill("Toán");
  await sourceDialog.getByLabel("Khối lớp").fill("12");
  await sourceDialog
    .getByLabel("Nội dung tài liệu")
    .fill("Phương pháp giải và cách trình bày của giáo viên");
  const sourceResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/kiem-thu/du-an/${project._id}/nguon-tri-thuc`) &&
      response.request().method() === "POST",
  );
  await sourceDialog.getByRole("button", { name: "Thêm nguồn tri thức" }).click();
  expect((await sourceResponse).status()).toBe(201);
  const sourceRow = page.getByRole("row").filter({ hasText: `Nguồn giáo viên ${stamp}` });
  await expect(sourceRow).toBeVisible();
  const reindexResponse = page.waitForResponse(
    (response) =>
      /\/kiem-thu\/tai-lieu-yeu-cau\/[^/]+\/lap-chi-muc-lai$/.test(response.url()) &&
      response.request().method() === "POST",
  );
  await sourceRow.getByRole("button", { name: "Lập chỉ mục lại" }).click();
  expect((await reindexResponse).status()).toBe(202);
  await expect(sourceRow).toContainText(/Đã lập chỉ mục|Không thành công/);

  await page.goto(`/du-an/${project._id}/thuc-thi`);
  const planName = `Kế hoạch giao diện ${stamp}`;
  await page.getByRole("button", { name: "Tạo kế hoạch", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Tạo kế hoạch kiểm thử" })).toBeVisible();
  await page.getByLabel("Tên kế hoạch kiểm thử").fill(planName);
  await page.getByLabel("Mục tiêu kế hoạch kiểm thử").fill("Xác minh nút lưu kế hoạch");
  const planResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/kiem-thu/ke-hoach-kiem-thu") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Lưu kế hoạch" }).click();
  expect((await planResponse).status()).toBe(201);
  await expect(page.getByRole("cell", { name: planName, exact: true })).toBeVisible();
  const suiteName = `Bộ kiểm thử giao diện ${stamp}`;
  await page.getByRole("button", { name: "Tạo bộ kiểm thử", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Tạo bộ kiểm thử" })).toBeVisible();
  await page.getByLabel("Tên bộ kiểm thử").fill(suiteName);
  const suiteResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/kiem-thu/bo-kiem-thu") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Lưu bộ kiểm thử" }).click();
  expect((await suiteResponse).status()).toBe(201);
  await expect(page.getByRole("cell", { name: suiteName, exact: true })).toBeVisible();

  await page.goto(`/du-an/${project._id}/cai-dat`);
  const updatedName = `Button Integration Updated ${stamp}`;
  await page.getByLabel("Tên", { exact: true }).fill(updatedName);
  const settingsResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/kiem-thu/du-an/${project._id}/cai-dat`) &&
      response.request().method() === "PATCH",
  );
  await page.getByRole("button", { name: /Lưu với phiên bản/ }).click();
  expect((await settingsResponse).status()).toBe(200);
  const updatedProject = await qa(request, token, "GET", `/du-an/${project._id}`);
  expect(updatedProject.name).toBe(updatedName);

  await page.goto("/du-an");
  const missingProject = `Không tồn tại ${stamp}`;
  await page.getByLabel("Tìm dự án").fill(missingProject);
  await page.getByLabel("Tìm dự án").press("Enter");
  await expect(page.getByText("Không tìm thấy dự án phù hợp")).toBeVisible();
  await page.getByRole("button", { name: "Tạo dự án", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Tạo dự án" })).toBeVisible();
  await expectRuntimeClean(errors);
});
