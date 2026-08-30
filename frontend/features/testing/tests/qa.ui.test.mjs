import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const readSource = (path) => readFile(new URL(path, import.meta.url), "utf8");

const dataTableSource = await readSource("../components/DataTable.jsx");
const operationsSource = await readSource("../pages/OperationsPage.jsx");
const projectsSource = await readSource("../pages/ProjectsPage.jsx");

test("DataTable always assigns a unique key to desktop and mobile rows", () => {
  assert.doesNotMatch(dataTableSource, /key=\{item\._id \|\| item\.id\}/);
  assert.equal(dataTableSource.match(/key=\{rowKey\(item, index\)\}/g)?.length, 2);
  assert.match(dataTableSource, /item\._id \?\? item\.id \?\? item\.key \?\? item\.code/);
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
