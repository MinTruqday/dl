"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  createUserAPI,
  getUsersAPI,
  updateUserRoleAPI,
  updateUserStatusAPI,
} from "@/features/humanity/services/user.service";
import {
  updateUserKycAPI,
  updateUserShadowbanAPI,
} from "@/features/management/services/user-moderation.service";

export type ManagedUser = {
  _id?: string;
  id?: string;
  email?: string;
  full_name?: string;
  slug?: string;
  role?: string;
  is_active?: boolean;
  is_shadowbanned?: boolean;
  kyc_status?: string;
  created_at?: string;
};

export type UserChange = {
  user: ManagedUser;
  field: "role" | "is_active" | "is_shadowbanned" | "kyc_status";
  value: string | boolean;
};

export function useUsers(query: string, role: string) {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!allowed) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await getUsersAPI(100, 0);
      const data = response?.data || response || [];
      setUsers(Array.isArray(data) ? data : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải người dùng",
      );
    } finally {
      setLoading(false);
    }
  }, [allowed]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(
    () =>
      users.filter((item) => {
        const matchesRole =
          role === "all" ||
          String(item.role || "reader").toLowerCase() === role;
        const value = query.trim().toLocaleLowerCase("vi");
        return (
          matchesRole &&
          (!value ||
            `${item.full_name || ""} ${item.email || ""} ${item.slug || ""}`
              .toLocaleLowerCase("vi")
              .includes(value))
        );
      }),
    [query, role, users],
  );

  const update = async (change: UserChange) =>
    mutate(async () => {
      const id = change.user._id || change.user.id || "";
      if (change.field === "role")
        await updateUserRoleAPI(id, String(change.value));
      if (change.field === "is_active")
        await updateUserStatusAPI(id, Boolean(change.value));
      if (change.field === "is_shadowbanned")
        await updateUserShadowbanAPI(id, Boolean(change.value));
      if (change.field === "kyc_status")
        await updateUserKycAPI(
          id,
          change.value as "PENDING" | "VERIFIED" | "REJECTED",
        );
    });

  const create = async (values: {
    email: string;
    password: string;
    full_name: string;
    role: string;
  }) => {
    if (values.password.length < 12) {
      setError("Mật khẩu cần ít nhất 12 ký tự");
      return false;
    }
    return mutate(() => createUserAPI(values));
  };

  async function mutate(action: () => Promise<any>) {
    if (processing) return false;
    setProcessing(true);
    setError("");
    try {
      await action();
      await load();
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật người dùng",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  }

  return {
    users: visible,
    total: users.length,
    allowed,
    loading: authLoading || loading,
    processing,
    error,
    reload: load,
    update,
    create,
  };
}
