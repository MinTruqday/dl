"use client";

import EditorPage from "@/features/content/components/EditorPage";
import { Suspense } from "react";

function SoanThaoContent() {
  return <EditorPage />;
}

export default function Page() {
  return (
    <Suspense>
      <SoanThaoContent />
    </Suspense>
  );
}
