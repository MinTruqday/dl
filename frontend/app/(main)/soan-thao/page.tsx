"use client";

import { useSearchParams } from "next/navigation";
import EditorPage from "@/features/content/components/EditorPage";
import CreateDocumentPage from "@/features/content/components/CreateDocumentPage";
import ProvisionLayout from "@/features/content/components/ProvisionLayout";
import { Suspense } from "react";

function SoanThaoContent() {
  const searchParams = useSearchParams();
  const documentId = searchParams.get("tai-lieu");

  if (documentId) {
    return <EditorPage />;
  }

  return (
    <ProvisionLayout>
      <CreateDocumentPage />
    </ProvisionLayout>
  );
}

export default function Page() {
  return (
    <Suspense>
      <SoanThaoContent />
    </Suspense>
  );
}
