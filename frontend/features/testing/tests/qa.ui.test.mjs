import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const dataTableSource = await readSource("../components/DataTable.jsx");
const appShellSource = await readSource("../../../shared/components/layout/AppShell.jsx");
const modalSource = await readSource("../../../shared/components/ui/Modal.jsx");
const buttonSource = await readSource("../../../shared/components/ui/Button.jsx");
const authFrameSource = await readSource("../../authentication/components/AuthFrame.jsx");
const testingUiSource = await readSource("../components/TestingUi.jsx");
const operationsSource = await readSource("../pages/OperationsPage.jsx");
const projectsSource = await readSource("../pages/ProjectsPage.jsx");
const requirementsSource = await readSource("../pages/workspace/RequirementsPage.jsx");
const changesSource = await readSource("../pages/workspace/ChangesPage.jsx");
const executionSource = await readSource("../pages/workspace/ExecutionPage.jsx");
const defectsSource = await readSource("../pages/workspace/DefectsPage.jsx");
const testDesignSource = await readSource("../pages/workspace/TestDesignPage.jsx");
const templatePanelSource = await readSource("../components/TestCaseTemplatesPanel.jsx");
const deviceMatricesSource = await readSource("../components/DeviceMatricesPanel.jsx");
const projectNotificationsSource = await readSource("../components/ProjectNotificationsPanel.jsx");
const specializedDesignSource = await readSource("../components/SpecializedDesignPanel.jsx");
const automationScriptsSource = await readSource("../components/AutomationScriptsPanel.jsx");
const webhookSource = await readSource("../components/WebhookPanel.jsx");
const projectConnectorsSource = await readSource("../components/ProjectConnectorsPanel.jsx");
const automationExecutionSource = await readSource("../components/AutomationExecutionPanel.jsx");
const cicdSource = await readSource("../components/CicdPanel.jsx");
const collaborationSource = await readSource("../components/CollaborationPanel.jsx");
const settingsSource = await readSource("../pages/workspace/SettingsPage.jsx");
const testingServiceSource = await readSource("../services/testing.service.js");

test("DataTable always assigns a unique key to desktop and mobile rows", () => {
  assert.doesNotMatch(dataTableSource, /key=\{item\._id \|\| item\.id\}/);
  assert.equal(dataTableSource.match(/key=\{rowKey\(item, index\)\}/g)?.length, 2);
  assert.match(dataTableSource, /item\._id \?\? item\.id \?\? item\.key \?\? item\.code/);
});

test("shared navigation and tables remain operable with keyboard and mobile focus", () => {
  assert.match(appShellSource, /aria-controls="mobile-navigation"/);
  assert.match(appShellSource, /aria-expanded=\{mobileOpen\}/);
  assert.match(appShellSource, /document\.body\.style\.overflow = "hidden"/);
  assert.match(appShellSource, /drawer\.querySelectorAll\(focusableSelector\)/);
  assert.match(appShellSource, /role="menu"/);
  assert.match(dataTableSource, /openFromKeyboard/);
  assert.equal(dataTableSource.match(/tabIndex=\{onSelect \? 0 : undefined\}/g)?.length, 2);
  assert.match(dataTableSource, /Chọn tất cả trên trang/);
  assert.match(dataTableSource, /event\.stopPropagation\(\)/);
});

test("shared modal has an accessible name and its close control never submits a form", () => {
  assert.match(modalSource, /aria-label=\{ariaLabel\}/);
  assert.match(modalSource, /type="button"\s+onClick=\{onClose\}/);
});

test("shared buttons do not submit forms unless a caller explicitly requests it", () => {
  assert.match(buttonSource, /<button\s+type="button"/);
  assert.match(buttonSource, /type="button"[\s\S]*\{\.\.\.props\}/);
});

test("authentication screens contain only the form instead of promotional filler", () => {
  assert.doesNotMatch(authFrameSource, /Chức năng chính/);
  assert.doesNotMatch(authFrameSource, /Quản lý yêu cầu và phiên bản/);
  assert.match(authFrameSource, /items-center justify-center/);
});

test("testing workspaces use the available width without compressing dense tables", () => {
  assert.match(appShellSource, /const fullWidthRoutes = \["\/du-an", "\/van-hanh"\]/);
  assert.match(dataTableSource, /columns\.length \* 150/);
  assert.match(testingUiSource, /break-words text-\[30px\]/);
  assert.match(testingUiSource, /min-w-0 flex-1/);
});

test("project creation fields use a stable full width layout", () => {
  assert.doesNotMatch(projectsSource, /Quản lý yêu cầu, kịch bản kiểm thử/);
  assert.match(projectsSource, /field-label block min-w-0/);
  assert.match(projectsSource, /apple-input mt-2 w-full/);
  assert.match(projectsSource, /min-h-24 w-full resize-y/);
});

test("operations copy is Vietnamese and model identifiers have readable labels", () => {
  for (const phrase of [
    "Job nhập liệu lỗi",
    "Job worker lỗi",
    "Worker failure",
    "Tìm trong audit",
    "Không có audit phù hợp",
    ">Retry<",
    "Backlog lập chỉ mục knowledge",
  ]) {
    assert.ok(!operationsSource.includes(phrase), phrase);
  }
  for (const phrase of [
    "Phân tích ảnh hưởng",
    "Đề xuất bảo trì",
    "Kiểm thử hồi quy",
    "Mô hình tác tử kết hợp phiên bản 1",
    "Mô hình bảo trì phiên bản 1",
    "Mô hình chấm điểm rủi ro phiên bản 1",
    "Nhật ký hệ thống",
    "Lỗi xử lý nền",
  ]) {
    assert.ok(operationsSource.includes(phrase), phrase);
  }
});

test("requirement composition actions call canonical Vietnamese routes and retain human gates", () => {
  for (const route of [
    "/du-an/${projectId}/yeu-cau/${requirementId}/tach",
    "/du-an/${projectId}/yeu-cau/gop",
    "/du-an/${projectId}/yeu-cau/kiem-tra-trung-lap",
    "/nhap-yeu-cau/${id}/ung-vien/gop",
    "/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tach",
    "/nhap-yeu-cau/${id}/ung-vien/${candidateId}/tu-choi",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Tách yêu cầu đã phê duyệt",
    "Xác nhận tách",
    "Gộp các yêu cầu đã phê duyệt",
    "Xác nhận gộp",
    "Ứng viên yêu cầu trùng lặp",
    "Từ chối ứng viên yêu cầu",
    "Từ chối mục đã chọn",
  ]) {
    assert.ok(requirementsSource.includes(label), label);
  }
  assert.match(
    requirementsSource,
    /current\.status === "BASELINED" && can\("requirement\.split"\)/,
  );
});

test("impact rerun creates a new snapshot and keeps review override controls", () => {
  assert.ok(testingServiceSource.includes("/phan-tich-anh-huong/${id}/chay-lai"));
  for (const label of [
    "Chạy lại phân tích ảnh hưởng",
    "Tạo snapshot mới",
    "Chạy lại thành snapshot mới",
    "Duyệt phân tích",
  ]) {
    assert.ok(changesSource.includes(label), label);
  }
  assert.match(changesSource, /expected_revision: impact\.revision/);
  assert.match(changesSource, /overrides: payload/);
});

test("test case template repository exposes the complete project lifecycle", () => {
  for (const route of [
    "/du-an/${projectId}/mau-ca-kiem-thu",
    "/mau-ca-kiem-thu/${templateId}",
    "/mau-ca-kiem-thu/${templateId}/luu-tru",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Mẫu ca kiểm thử",
    "Chức năng",
    "API",
    "Phân quyền RBAC",
    "Chuyển trạng thái",
    "Giá trị biên BVA",
    "Tạo mẫu",
    "Chỉnh sửa",
    "Lưu trữ",
  ]) {
    assert.ok(templatePanelSource.includes(label), label);
  }
  assert.match(testDesignSource, /can\("testcase\.template\.read"\)/);
  assert.match(templatePanelSource, /expected_revision: selected\.revision/);
  assert.match(templatePanelSource, /testcase\.template\.manage/);
  assert.match(templatePanelSource, /tester_can_archive_testcase_templates === true/);
  assert.match(settingsSource, /"testcase\.template\.archive"/);
});

test("run resume preserves frozen scope and not applicable results retain policy gates", () => {
  assert.ok(
    testingServiceSource.includes("/du-an/${projectId}/lan-chay-kiem-thu/${runId}/tiep-tuc"),
  );
  for (const label of [
    "Tiếp tục thực thi",
    "Vị trí tiếp tục",
    "Ghi nhận kết quả Không áp dụng",
    "Lý do Không áp dụng",
    "Mỗi bước Không áp dụng phải có lý do riêng",
  ]) {
    assert.ok(executionSource.includes(label), label);
  }
  assert.match(executionSource, /expected_revision: run\.revision/);
  assert.match(executionSource, /project\.settings\?\.allow_not_applicable_results/);
  assert.match(settingsSource, /allow_not_applicable_results/);
});

test("bug trace suggestions remain candidates until a separate human confirmation", () => {
  for (const route of [
    "/du-an/${projectId}/ai/loi/${defectId}/goi-y-truy-vet",
    "/du-an/${projectId}/loi/${defectId}/truy-vet",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Yêu cầu được đề xuất",
    "Ca kiểm thử được đề xuất",
    "Xác nhận liên kết truy vết",
    "Lý do xác nhận",
  ]) {
    assert.ok(defectsSource.includes(label), label);
  }
  assert.match(defectsSource, /can\("ai\.suggest_bug_trace"\)/);
  assert.match(defectsSource, /Không tự\s+động thay đổi lỗi/);
  assert.match(defectsSource, /ai_result_id: traceReview\.result\._id/);
  assert.match(defectsSource, /accepted_candidate_ids: \[candidate\.candidate_id\]/);
});

test("bulk actions use canonical permissions and carry idempotency for safe replay", () => {
  assert.match(testDesignSource, /can\("testcase\.bulk\.update"\)/);
  assert.match(testDesignSource, /can\("testcase\.bulk\.archive"\)/);
  assert.match(testDesignSource, /idempotency_key: crypto\.randomUUID\(\)/);
  assert.match(testingServiceSource, /bulkTags: \(projectId, payload\)/);
  assert.match(testingServiceSource, /bulkApproveProposals: \(projectId, payload\)/);
  for (const method of [
    "previewBulkTags",
    "previewBulkAddToSuite",
    "previewBulkMarkReviewRequired",
    "previewBulkArchive",
    "previewBulkGenerateProposals",
    "previewBulkApproveProposals",
  ]) {
    assert.match(testingServiceSource, new RegExp(`${method}:`), method);
  }
});

test("device matrices connect creation assignment and frozen execution scope", () => {
  for (const route of [
    "/du-an/${id}/ma-tran-thiet-bi",
    "/du-an/${projectId}/ma-tran-thiet-bi",
    "/ma-tran-thiet-bi/${id}/gan",
    "/ma-tran-thiet-bi/${id}/luu-tru",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Ma trận thiết bị",
    "Tạo ma trận",
    "Gán ma trận thiết bị",
    "Hồ sơ thiết bị",
  ]) {
    assert.ok(deviceMatricesSource.includes(label), label);
  }
  assert.match(deviceMatricesSource, /device_matrix\.manage/);
  assert.match(deviceMatricesSource, /device_matrix\.assign/);
  assert.match(executionSource, /<DeviceMatricesPanel/);
});

test("proposal acceptance uses the canonical Vietnamese contract", () => {
  assert.match(testingServiceSource, /chap-nhan-co-chinh-sua/);
  assert.match(testingServiceSource, /chap-nhan/);
  assert.doesNotMatch(testingServiceSource, /accept-with-edit/);
});

test("project notification workflow preserves self service and project rule boundaries", () => {
  for (const route of [
    "/du-an/${projectId}/thong-bao/theo-doi",
    "/du-an/${projectId}/thong-bao/theo-doi/${artifactType}/${artifactId}",
    "/du-an/${projectId}/thong-bao/quy-tac",
    "/du-an/${projectId}/thong-bao/tuy-chon",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Thông báo dự án",
    "Dữ liệu đang theo dõi",
    "Tùy chọn cá nhân",
    "Quy tắc dự án",
    "Bỏ theo dõi",
  ]) {
    assert.ok(projectNotificationsSource.includes(label), label);
  }
  assert.match(projectNotificationsSource, /notification\.watch\.manage/);
  assert.match(projectNotificationsSource, /notification\.preferences\.manage/);
  assert.match(projectNotificationsSource, /notification\.project_rule\.manage/);
  assert.match(settingsSource, /<ProjectNotificationsPanel/);
});

test("specialized AI design stays draft only and exposes degraded results", () => {
  for (const route of [
    "/du-an/${projectId}/ai/goi-y-kiem-thu-bao-mat",
    "/du-an/${projectId}/ai/ke-hoach-hieu-nang",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Thiết kế kiểm thử chuyên sâu",
    "Gợi ý kiểm thử bảo mật",
    "Bản nháp kế hoạch hiệu năng",
    "quét lỗ hổng hoặc phát",
    "chưa thực thi phát tải",
  ]) {
    assert.ok(specializedDesignSource.includes(label), label);
  }
  assert.match(specializedDesignSource, /ai\.generate_security_tests/);
  assert.match(specializedDesignSource, /ai\.generate_performance_plan/);
  assert.match(specializedDesignSource, /generation_status/);
  assert.match(testDesignSource, /<SpecializedDesignPanel/);
});

test("project webhook workflow uses platform references and explicit replay", () => {
  for (const route of [
    "/du-an/${projectId}/moc-goi",
    "/du-an/${projectId}/moc-goi/${subscriptionId}",
    "/du-an/${projectId}/moc-goi/giao-hang",
    "/du-an/${projectId}/moc-goi/giao-hang/${deliveryId}/phat-lai",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Móc gọi dự án",
    "Tạo đăng ký móc gọi",
    "Phát lại lần giao móc gọi",
    "Đưa vào hàng đợi",
  ]) {
    assert.ok(webhookSource.includes(label), label);
  }
  assert.match(webhookSource, /endpoint:\/\//);
  assert.match(webhookSource, /secret:\/\//);
  assert.match(webhookSource, /webhook\.project\.manage/);
  assert.match(webhookSource, /webhook\.project\.replay/);
  assert.match(settingsSource, /<WebhookPanel/);
});

test("automation script workflow keeps editing approval and export as separate gates", () => {
  for (const route of [
    "/du-an/${projectId}/ban-nhap-kich-ban-tu-dong",
    "/du-an/${projectId}/ai/ban-nhap-kich-ban-tu-dong",
    "/ban-nhap-kich-ban-tu-dong/${draftId}",
    "/ban-nhap-kich-ban-tu-dong/${draftId}/phe-duyet",
    "/ban-nhap-kich-ban-tu-dong/${draftId}/xuat",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Kịch bản kiểm thử tự động hóa",
    "Không ghi kho mã nguồn",
    "Lưu bản nháp",
    "Phê duyệt kịch bản",
    "Xuất tệp đã duyệt",
  ]) {
    assert.ok(automationScriptsSource.includes(label), label);
  }
  assert.match(automationScriptsSource, /ai\.generate_automation_script/);
  assert.match(automationScriptsSource, /automation\.script\.approve/);
  assert.match(automationScriptsSource, /selected\.status === "APPROVED" && canExport/);
  assert.match(automationScriptsSource, /generation_status/);
  assert.match(testDesignSource, /<AutomationScriptsPanel/);
});

test("project connectors use platform references versioned mappings and explicit conflict review", () => {
  for (const route of [
    "/du-an/${projectId}/ket-noi",
    "/du-an/${projectId}/ket-noi/${connectorId}",
    "/du-an/${projectId}/ket-noi/${connectorId}/ngat",
    "/du-an/${projectId}/ket-noi/${connectorId}/dong-bo",
    "/du-an/${projectId}/ket-noi/nhat-ky",
    "/du-an/${projectId}/ket-noi/xung-dot",
    "/du-an/${projectId}/ket-noi/xung-dot/${conflictId}/giai-quyet",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const label of [
    "Kết nối dự án",
    "Tham chiếu kết nối nền tảng",
    "Lưu phiên bản ánh xạ",
    "Đồng bộ thủ công",
    "Giải quyết xung đột đồng bộ",
  ]) {
    assert.ok(projectConnectorsSource.includes(label), label);
  }
  assert.match(projectConnectorsSource, /connector:\/\/platform\//);
  assert.match(projectConnectorsSource, /project\.connector\.manage/);
  assert.match(projectConnectorsSource, /project\.connector\.review/);
  assert.match(settingsSource, /<ProjectConnectorsPanel/);
});

test("automated execution CI CD and collaboration services use canonical Vietnamese contracts", () => {
  for (const route of [
    "/du-an/${projectId}/thuc-thi-tu-dong",
    "/thuc-thi-tu-dong/${executionId}/bat-dau",
    "/thuc-thi-tu-dong/${executionId}/huy",
    "/thuc-thi-tu-dong/${executionId}/bang-chung",
    "/du-an/${projectId}/tich-hop-trien-khai-lien-tuc",
    "/du-an/${projectId}/tich-hop-trien-khai-lien-tuc/lan-chay/${runId}/thu-lai",
    "/du-an/${projectId}/cong-tac/phien",
    "/du-an/${projectId}/cong-tac/hien-dien",
    "/du-an/${projectId}/cong-tac/yeu-cau/${artifactId}/thao-tac",
    "/du-an/${projectId}/cong-tac/ca-kiem-thu/${artifactId}/thao-tac",
    "/du-an/${projectId}/cong-tac/xung-dot",
    "/du-an/${projectId}/cong-tac/xung-dot/${conflictId}/giai-quyet",
  ]) {
    assert.ok(testingServiceSource.includes(route), route);
  }
  for (const englishRoute of ["/automation", "/pipeline", "/collaboration", "/presence"])
    assert.ok(!testingServiceSource.includes(englishRoute), englishRoute);
  for (const label of [
    "Thực thi Newman",
    "Tạo lần chạy Newman",
    "Bắt đầu Newman",
    "Hủy tác vụ",
    "Tải evidence",
  ])
    assert.ok(automationExecutionSource.includes(label), label);
  for (const label of [
    "Tích hợp CI CD",
    "Ánh xạ pipeline",
    "Thử đối soát lại",
    "danh tính dịch vụ có chữ ký",
  ])
    assert.ok(cicdSource.includes(label), label);
  for (const label of [
    "Cộng tác trên bản nháp",
    "Đang mở bản nháp",
    "Xung đột cần rà soát",
    "Giải quyết xung đột",
  ])
    assert.ok(collaborationSource.includes(label), label);
  assert.match(executionSource, /<AutomationExecutionPanel/);
  assert.match(settingsSource, /<CicdPanel/);
  assert.match(requirementsSource, /applyRequirementCollaborationOperation/);
  assert.match(testDesignSource, /applyTestCaseCollaborationOperation/);
  assert.match(requirementsSource, /<CollaborationPanel/);
  assert.match(testDesignSource, /<CollaborationPanel/);
});
