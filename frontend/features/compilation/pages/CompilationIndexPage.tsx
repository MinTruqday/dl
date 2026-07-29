"use client";

import { useSearchParams, redirect } from "next/navigation";
import EditorPage from "@/features/content/components/EditorPage";
import { Suspense, useEffect } from "react";

function SoanThaoContent() {
  const searchParams = useSearchParams();
  const documentId = searchParams.get("tai-lieu");

  useEffect(() => {
    if (!documentId) {
      redirect("/soan-thao/khoi-tao");
    }
  }, [documentId]);

  if (documentId) {
    return <EditorPage />;
  }

  return null;
}

export default function Page() {
  return (
    <Suspense>
      <SoanThaoContent />
    </Suspense>
  );
}
