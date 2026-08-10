"use client";

import { Suspense } from "react";
import PageLoader from "@/shared/components/common/PageLoader";
import EditorWorkspace from "@/features/compilation/components/EditorWorkspace";

export default function EditorPage() {
  return (
    <Suspense fallback={<PageLoader rows={8} />}>
      <EditorWorkspace />
    </Suspense>
  );
}
