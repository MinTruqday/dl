"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { API_URL } from "@/shared/services/api-client";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import { updateMyProfileAPI } from "@/features/humanity/services/account.service";

export function useProfile() {
  const { user, isLoading, logoutState, refreshUser } = useAuth() as any;
  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [processing, setProcessing] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name || "");
    setBio(user.bio || "");
    setAvatarUrl(user.avatar_url || "");
  }, [user]);

  const save = async () => {
    if (processing) return;
    setProcessing("save");
    setError("");
    setNotice("");
    try {
      await updateMyProfileAPI({
        full_name: fullName.trim(),
        bio: bio.trim(),
        avatar_url: avatarUrl,
      });
      await refreshUser();
      setNotice("Đã lưu hồ sơ");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể lưu hồ sơ",
      );
    } finally {
      setProcessing("");
    }
  };

  const uploadAvatar = async (file: File) => {
    if (processing) return;
    setProcessing("avatar");
    setError("");
    setNotice("");
    try {
      const response = await uploadAssetAPI(file, "image");
      const value = response?.data?.url || response?.url;
      if (!value) throw new Error("Backend không trả về đường dẫn ảnh");
      const url = value.startsWith("http")
        ? value
        : `${API_URL}/tai-len/luu-tru/${value}`;
      setAvatarUrl(url);
      await updateMyProfileAPI({ avatar_url: url });
      await refreshUser();
      setNotice("Đã cập nhật ảnh đại diện");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải ảnh đại diện",
      );
    } finally {
      setProcessing("");
    }
  };

  return {
    user,
    loading: isLoading,
    fullName,
    setFullName,
    bio,
    setBio,
    avatarUrl,
    processing,
    error,
    notice,
    save,
    uploadAvatar,
    logout: logoutState,
  };
}
