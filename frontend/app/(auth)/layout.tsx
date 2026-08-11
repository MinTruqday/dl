import { Suspense } from "react";
import AuthLoading from "@/features/authentication/components/AuthLoading";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Suspense fallback={<AuthLoading />}>{children}</Suspense>;
}

