"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import { Button } from "@/shared/components/ui/Button";
import { getProtectedDocumentPageAPI } from "@/features/content/services/document.service";

type Props = {
  documentId: string;
  password?: string;
  shareToken?: string;
  zoom: number;
};

export default function ProtectedPdfViewer({
  documentId,
  password,
  shareToken,
  zoom,
}: Props) {
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let objectUrl = "";
    setLoading(true);
    setError("");
    getProtectedDocumentPageAPI(documentId, page, password, shareToken)
      .then((result) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(result.blob);
        setImageUrl(objectUrl);
        setPageCount(result.pageCount);
      })
      .catch((cause) => {
        if (active)
          setError(
            cause instanceof Error ? cause.message : "Không thể tải trang tài liệu",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [documentId, page, password, shareToken]);

  if (error) return <InlineState title="Không thể mở trang tài liệu" detail={error} tone="danger" />;

  return (
    <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col items-center gap-4">
      <div className="sticky top-0 z-10 flex items-center gap-2 rounded-control border border-border bg-surface p-1 shadow-sm">
        <Button
          size="icon"
          variant="ghost"
          aria-label="Trang trước"
          disabled={page <= 1 || loading}
          onClick={() => setPage((value) => Math.max(1, value - 1))}
        >
          <ChevronLeft size={16} />
        </Button>
        <span className="min-w-20 text-center text-[12px] text-ink-muted">
          {page} / {pageCount}
        </span>
        <Button
          size="icon"
          variant="ghost"
          aria-label="Trang sau"
          disabled={page >= pageCount || loading}
          onClick={() => setPage((value) => Math.min(pageCount, value + 1))}
        >
          <ChevronRight size={16} />
        </Button>
      </div>
      {loading ? (
        <div className="h-[720px] w-full animate-pulse rounded-workspace bg-surface-raised" />
      ) : (
        <img
          src={imageUrl}
          alt={`Trang ${page}`}
          draggable={false}
          className="origin-top rounded-workspace border border-border bg-white shadow-sm"
          style={{ width: `${zoom}%`, maxWidth: "none" }}
        />
      )}
    </div>
  );
}
