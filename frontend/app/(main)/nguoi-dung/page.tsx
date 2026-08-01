"use client";

import { useState } from "react";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import { ManagedUser, UserChange, useUsers } from "./useUsers";

type RoleFilter = "all" | "reader" | "author" | "admin";

const roleLabels: Record<string, string> = {
  reader: "Độc giả",
  author: "Tác giả",
  admin: "Quản trị viên",
};

export default function UsersPage() {
  const [role, setRole] = useState<RoleFilter>("all");
  const [query, setQuery] = useState("");
  const [change, setChange] = useState<UserChange | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "reader",
  });
  const users = useUsers(query, role);

  if (users.loading) return <PageLoader rows={7} />;
  if (!users.allowed)
    return (
      <InlineState
        title="Không có quyền truy cập"
        detail="Trang này chỉ dành cho quản trị viên"
        tone="danger"
      />
    );

  const confirmChange = async () => {
    if (!change) return;
    if (await users.update(change)) setChange(null);
  };

  const create = async () => {
    if (!form.full_name.trim() || !form.email.trim() || !form.password) return;
    if (await users.create(form)) {
      setCreateOpen(false);
      setForm({ full_name: "", email: "", password: "", role: "reader" });
    }
  };

  const requestChange = (
    user: ManagedUser,
    field: UserChange["field"],
    value: UserChange["value"],
  ) => setChange({ user, field, value });

  return (
    <div className="w-full">
      <PageHeader
        title="Người dùng"
        meta={`${users.total} tài khoản`}
        actions={
          <>
            <Button variant="secondary" onClick={users.reload}>
              Làm mới
            </Button>
            <Button onClick={() => setCreateOpen(true)}>Thêm người dùng</Button>
          </>
        }
      />
      {users.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể cập nhật người dùng"
            detail={users.error}
            tone="danger"
          />
        </div>
      )}
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <SegmentedTabs<RoleFilter>
          label="Lọc theo vai trò"
          value={role}
          onChange={setRole}
          tabs={[
            { id: "all", label: "Tất cả" },
            { id: "reader", label: "Độc giả" },
            { id: "author", label: "Tác giả" },
            { id: "admin", label: "Quản trị" },
          ]}
        />
        <div className="w-full lg:max-w-xs">
          <label
            htmlFor="user-search"
            className="mb-2 block text-[12px] font-semibold text-ink-muted"
          >
            Tìm người dùng
          </label>
          <input
            id="user-search"
            type="search"
            className="apple-input w-full"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </div>

      {!users.users.length ? (
        <EmptyState
          text="Không tìm thấy người dùng"
          description="Thử vai trò hoặc từ khóa khác"
        />
      ) : (
        <div className="overflow-x-auto rounded-panel border border-border bg-surface">
          <table className="w-full min-w-[900px] border-collapse text-left">
            <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
              <tr>
                <th className="px-4 py-3">Người dùng</th>
                <th className="px-4 py-3">Vai trò</th>
                <th className="px-4 py-3">Xác minh</th>
                <th className="px-4 py-3">Hiển thị</th>
                <th className="px-4 py-3">Tài khoản</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.users.map((user) => {
                const id = user._id || user.id || "";
                return (
                  <tr key={id} className="text-[13px] hover:bg-surface-raised">
                    <td className="max-w-xs px-4 py-3.5">
                      <p className="truncate font-semibold text-ink">
                        {user.full_name || "Chưa có tên"}
                      </p>
                      <p className="mt-1 truncate text-ink-muted">
                        {user.email}
                      </p>
                    </td>
                    <td className="px-4 py-3.5">
                      <select
                        aria-label={`Vai trò của ${user.full_name || user.email}`}
                        className="apple-input min-h-9 py-1.5 text-[13px]"
                        value={user.role || "reader"}
                        onChange={(event) =>
                          requestChange(user, "role", event.target.value)
                        }
                      >
                        <option value="reader">Độc giả</option>
                        <option value="author">Tác giả</option>
                        <option value="admin">Quản trị viên</option>
                      </select>
                    </td>
                    <td className="px-4 py-3.5">
                      <select
                        aria-label={`Xác minh của ${user.full_name || user.email}`}
                        className="apple-input min-h-9 py-1.5 text-[13px]"
                        value={user.kyc_status || "PENDING"}
                        onChange={(event) =>
                          requestChange(user, "kyc_status", event.target.value)
                        }
                      >
                        <option value="PENDING">Đang chờ</option>
                        <option value="VERIFIED">Đã xác minh</option>
                        <option value="REJECTED">Từ chối</option>
                      </select>
                    </td>
                    <td className="px-4 py-3.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          requestChange(
                            user,
                            "is_shadowbanned",
                            !user.is_shadowbanned,
                          )
                        }
                      >
                        {user.is_shadowbanned ? "Cho hiển thị" : "Ẩn nội dung"}
                      </Button>
                    </td>
                    <td className="px-4 py-3.5">
                      <Button
                        variant={
                          user.is_active === false ? "secondary" : "ghost"
                        }
                        size="sm"
                        onClick={() =>
                          requestChange(
                            user,
                            "is_active",
                            user.is_active === false,
                          )
                        }
                      >
                        {user.is_active === false ? "Kích hoạt" : "Tạm khóa"}
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        isOpen={Boolean(change)}
        onClose={() => !users.processing && setChange(null)}
      >
        <ModalHeader>
          <ModalTitle>Xác nhận thay đổi</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            Thay đổi sẽ áp dụng cho{" "}
            {change?.user.full_name || change?.user.email}
          </p>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setChange(null)}
            disabled={users.processing}
          >
            Hủy
          </Button>
          <Button onClick={confirmChange} disabled={users.processing}>
            {users.processing ? "Đang cập nhật" : "Xác nhận"}
          </Button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={createOpen}
        onClose={() => !users.processing && setCreateOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>Thêm người dùng</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="new-user-name"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Tên hiển thị
              </label>
              <input
                id="new-user-name"
                className="apple-input w-full"
                value={form.full_name}
                onChange={(event) =>
                  setForm({ ...form, full_name: event.target.value })
                }
              />
            </div>
            <div>
              <label
                htmlFor="new-user-email"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Email
              </label>
              <input
                id="new-user-email"
                type="email"
                className="apple-input w-full"
                value={form.email}
                onChange={(event) =>
                  setForm({ ...form, email: event.target.value })
                }
              />
            </div>
            <div>
              <label
                htmlFor="new-user-password"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Mật khẩu
              </label>
              <input
                id="new-user-password"
                type="password"
                minLength={12}
                className="apple-input w-full"
                value={form.password}
                onChange={(event) =>
                  setForm({ ...form, password: event.target.value })
                }
              />
              <p className="mt-2 text-[12px] text-ink-muted">
                Tối thiểu 12 ký tự
              </p>
            </div>
            <div>
              <label
                htmlFor="new-user-role"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Vai trò
              </label>
              <select
                id="new-user-role"
                className="apple-input w-full"
                value={form.role}
                onChange={(event) =>
                  setForm({ ...form, role: event.target.value })
                }
              >
                <option value="reader">Độc giả</option>
                <option value="author">Tác giả</option>
                <option value="admin">Quản trị viên</option>
              </select>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setCreateOpen(false)}
            disabled={users.processing}
          >
            Hủy
          </Button>
          <Button
            onClick={create}
            disabled={
              users.processing ||
              !form.full_name ||
              !form.email ||
              form.password.length < 12
            }
          >
            {users.processing ? "Đang tạo" : "Tạo tài khoản"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
