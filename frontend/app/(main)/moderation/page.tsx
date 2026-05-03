"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ModeratorIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/moderator/documents");
  }, [router]);

  return null;
}
