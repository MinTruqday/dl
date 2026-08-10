"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import { useCreateDocument } from "../hooks/useCreateDocument";
import ComposerNavigation from "../components/ComposerNavigation";

export default function CreateDocumentPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<"public" | "private">("public");
  const [contentFormat, setContentFormat] = useState<"doclib" | "doclibx">(
    "doclib",
  );
  useEffect(() => {
    const format = new URLSearchParams(window.location.search).get("dinh-dang");
    if (format === "latex") setContentFormat("doclibx");
    if (format === "json") setContentFormat("doclib");
  }, []);
  const {
    user,
    authorName,
    setAuthorName,
    publisherName,
    setPublisherName,
    submitting,
    error,
    submit,
  } = useCreateDocument();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit({
      title,
      description,
      authorName,
      publisherName,
      visibility,
      contentFormat,
    });
  };

  return (
    <div className="mx-auto w-full max-w-3xl">
      <ComposerNavigation />
      <PageHeader title="Tạo tài liệu" />
      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tạo tài liệu"
            detail={error}
            tone="danger"
          />
        </div>
      )}
      <form
        onSubmit={handleSubmit}
        className="space-y-7 rounded-workspace border border-border bg-surface p-5 md:p-7"
      >
        <div>
          <label
            htmlFor="document-title"
            className="mb-2 block text-[13px] font-semibold text-ink"
          >
            Tiêu đề
          </label>
          <input
            id="document-title"
            required
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="apple-input w-full"
            autoFocus
          />
        </div>
        <div>
          <label
            htmlFor="document-description"
            className="mb-2 block text-[13px] font-semibold text-ink"
          >
            Tóm tắt
          </label>
          <textarea
            id="document-description"
            maxLength={1200}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="apple-input min-h-28 w-full resize-y"
          />
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label
              htmlFor="document-author"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Tác giả
            </label>
            <input
              id="document-author"
              value={authorName}
              onChange={(event) => setAuthorName(event.target.value)}
              className="apple-input w-full"
            />
          </div>
          <div>
            <label
              htmlFor="document-publisher"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Nhà xuất bản
            </label>
            <input
              id="document-publisher"
              value={publisherName}
              onChange={(event) => setPublisherName(event.target.value)}
              className="apple-input w-full"
              disabled={user?.role === "admin"}
            />
          </div>
        </div>
        <fieldset>
          <legend className="mb-2 text-[13px] font-semibold text-ink">
            Định dạng
          </legend>
          <SegmentedTabs
            label="Chọn định dạng"
            value={contentFormat}
            onChange={setContentFormat}
            tabs={[
              { id: "doclib", label: "Tài liệu chuẩn" },
              { id: "doclibx", label: "LaTeX" },
            ]}
          />
        </fieldset>
        <fieldset>
          <legend className="mb-2 text-[13px] font-semibold text-ink">
            Quyền truy cập
          </legend>
          <SegmentedTabs
            label="Chọn quyền truy cập"
            value={visibility}
            onChange={setVisibility}
            tabs={[
              { id: "public", label: "Công khai" },
              { id: "private", label: "Riêng tư" },
            ]}
          />
        </fieldset>
        <div className="flex justify-end border-t border-border pt-5">
          <Button type="submit" disabled={submitting || !title.trim()}>
            {submitting ? "Đang tạo" : "Tạo tài liệu"}
          </Button>
        </div>
      </form>
    </div>
  );
}
