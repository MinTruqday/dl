"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { createDocumentAPI } from "@/features/content/services/document.service";

export type CreateDocumentValues = {
  title: string;
  description: string;
  authorName: string;
  publisherName: string;
  visibility: "public" | "private";
  contentFormat: "doclib" | "doclibx";
};

function slugify(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .replace(/[^a-z0-9]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export function useCreateDocument() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const [authorName, setAuthorName] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    const name = user.full_name || user.name || "";
    setAuthorName(name);
    setPublisherName(user.role === "admin" ? "DocLib" : name);
  }, [user]);

  const submit = async (values: CreateDocumentValues) => {
    if (submitting) return;
    if (!values.title.trim()) {
      setError("Nhập tiêu đề tài liệu");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const response = await createDocumentAPI({
        title: values.title.trim(),
        slug: `${slugify(values.title)}-${Date.now()}`,
        description: values.description.trim(),
        publisher_name: values.publisherName.trim(),
        visibility: values.visibility,
        content_format: values.contentFormat,
        status: "draft",
        author_name: values.authorName.trim(),
      });
      const data = response?.data || response || {};
      const id = data.id || data._id;
      if (!id) throw new Error("Backend không trả về mã tài liệu");
      router.push(`/soan-thao/chinh-sua?tai-lieu=${id}`);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tạo tài liệu",
      );
      setSubmitting(false);
    }
  };

  return {
    user,
    authorName,
    setAuthorName,
    publisherName,
    setPublisherName,
    submitting,
    error,
    submit,
  };
}
