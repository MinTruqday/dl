"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  logoutAPI,
  removeToken,
} from "@/features/authentication/services/session.service";
import {
  applyForAuthorAPI,
  deleteMyAccountAPI,
} from "@/features/humanity/services/account.service";
import {
  getPrivacySettingsAPI,
  updateGeneralSettingsAPI,
  updatePrivacySettingsAPI,
} from "@/features/humanity/services/setting.service";
import {
  getAnnouncementSettingsAPI,
  updateAnnouncementSettingsAPI,
} from "@/features/notification/services/announcement.service";

export type GeneralSettings = {
  auto_save: boolean;
  auto_refresh: boolean;
  default_visibility: "public" | "private" | "unlisted";
};
export type NotificationSettings = {
  enable_comment_notifications: boolean;
  enable_mention_notifications: boolean;
  enable_system_notifications: boolean;
  enable_email_digest: boolean;
};

const defaultNotifications: NotificationSettings = {
  enable_comment_notifications: true,
  enable_mention_notifications: true,
  enable_system_notifications: true,
  enable_email_digest: false,
};

export function useSettings() {
  const router = useRouter();
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const [general, setGeneral] = useState<GeneralSettings>({
    auto_save: true,
    auto_refresh: false,
    default_visibility: "public",
  });
  const [notifications, setNotifications] =
    useState<NotificationSettings>(defaultNotifications);
  const [privacyMode, setPrivacyMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    const results = await Promise.allSettled([
      getPrivacySettingsAPI(),
      getAnnouncementSettingsAPI(),
    ]);
    if (results[0].status === "fulfilled") {
      const value = results[0].value?.data || results[0].value || {};
      setPrivacyMode(Boolean(value.privacy_mode));
      setGeneral({
        auto_save: value.auto_save ?? user.settings?.auto_save ?? true,
        auto_refresh:
          value.auto_refresh ?? user.settings?.auto_refresh ?? false,
        default_visibility:
          value.default_visibility ||
          user.settings?.default_visibility ||
          "public",
      });
    }
    if (results[1].status === "fulfilled")
      setNotifications({
        ...defaultNotifications,
        ...(results[1].value?.data || results[1].value || {}),
      });
    setError(
      results.some((result) => result.status === "rejected")
        ? "Một phần cài đặt chưa tải được"
        : "",
    );
    setLoading(false);
  }, [user]);

  useEffect(() => {
    if (user) load();
  }, [load, user]);

  async function mutate(
    name: string,
    action: () => Promise<any>,
    success: string,
  ) {
    if (processing) return false;
    setProcessing(name);
    setError("");
    setNotice("");
    try {
      await action();
      await refreshUser();
      setNotice(success);
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể lưu cài đặt",
      );
      return false;
    } finally {
      setProcessing("");
    }
  }

  const saveGeneral = () =>
    mutate(
      "general",
      () => updateGeneralSettingsAPI(general),
      "Đã lưu cài đặt chung",
    );
  const saveNotifications = () =>
    mutate(
      "notifications",
      () => updateAnnouncementSettingsAPI(notifications),
      "Đã lưu cài đặt thông báo",
    );
  const savePrivacy = () =>
    mutate(
      "privacy",
      () => updatePrivacySettingsAPI({ privacy_mode: privacyMode }),
      "Đã lưu cài đặt riêng tư",
    );
  const applyAuthor = (motivation: string, portfolio: string) =>
    mutate(
      "author",
      () => applyForAuthorAPI(motivation, portfolio),
      "Đã gửi đơn ứng tuyển tác giả",
    );
  const deleteAccount = async () => {
    if (
      await mutate("delete", deleteMyAccountAPI, "Đã vô hiệu hóa tài khoản")
    ) {
      removeToken();
      router.replace("/dang-nhap");
    }
  };
  const logoutAll = async () => {
    if (
      await mutate(
        "sessions",
        () => logoutAPI(true),
        "Đã kết thúc mọi phiên đăng nhập",
      )
    ) {
      removeToken();
      router.replace("/dang-nhap");
    }
  };

  return {
    user,
    loading: authLoading || loading,
    processing,
    error,
    notice,
    general,
    setGeneral,
    notifications,
    setNotifications,
    privacyMode,
    setPrivacyMode,
    reload: load,
    saveGeneral,
    saveNotifications,
    savePrivacy,
    applyAuthor,
    deleteAccount,
    logoutAll,
  };
}
